import json
import logging
import sys

from datetime import datetime
from typing import Any, Tuple, Self
from dataclasses import dataclass

import requests
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from pathlib import Path


import subprocess
import pystac
import pyproj
import shapely.wkt
import shapely
import dask.bag as db
import logging
from dask.diagnostics import ProgressBar

from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.pointcloud import PointcloudExtension, Schema, Statistic

from .info import read_json

logger = logging.getLogger('wesm_stac')
# create console handler and set level to debug
ch = logging.StreamHandler(stream=sys.stdout)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
logger.setLevel(logging.INFO)

@dataclass
class WesmMetadata:
    FESMProjectID: str
    Entwined: bool
    EntwinePath: str
    LAZinCloud: bool
    FolderName: str
    workunit: str
    workunit_id: float
    project: str
    project_id: float
    collect_start: str
    collect_end: str
    ql: str
    spec: str
    p_method: str
    dem_gsd_meters: float
    horiz_crs: str
    vert_crs: str
    geoid: str
    lpc_pub_date: datetime
    lpc_category: str
    lpc_update: str
    lpc_reason: str
    sourcedem_pub_date: str
    sourcedem_update: str
    sourcedem_category: str
    sourcedem_reason: str
    onemeter_category: str
    onemeter_reason: str
    seamless_category: str
    seamless_reason: str
    lpc_link: str
    sourcedem_link: str
    metadata_link: str
    bbox: Tuple[float, float, float, float]

    def __post_init__(self):
        self.collect_end = get_date(self.collect_end)
        self.collect_start = get_date(self.collect_start)

        if self.lpc_link is None or not self.lpc_link:
            pass
        elif self.lpc_link[:-1] != '/':
            self.lpc_link = self.lpc_link + '/'

        if self.bbox:
            str_box = self.bbox.strip(' ').split(',')
            self.bbox = [float(v) for v in str_box]

# date collected
# WESM Docs say it should be YYYY-MM-DD (isoformat), but I'm also seeing
# YYYY/MM/DD, which is not isoformat so we're covering both.
def get_date(d:str) -> Any:
    try:
        dt = datetime.isoformat(d)
    except:
        try:
            dt = datetime.strptime(d, '%Y/%m/%d')
        except Exception as e:
            raise ValueError(f'Invalid datetime ({d}).', e)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

class MetaCatalog:
    """
    MetaCatalog reads the WESM JSON file at the given url, and creates a list of
    MetaCollections. Dask Bag helps facilitate the mapping of this in parallel.
    """
    def __init__(self, url: str, dst: str) -> None:
        self.url = url
        self.dst = dst
        self.children = [ ]
        self.catalog = pystac.Catalog(id='WESM Catalog',
            description='Catalog representing WESM metadata and associated'
                ' point cloud files.')
        self.catalog.set_root(self.catalog)
        self.obj: dict = read_json(self.url)

    def set_children(self, recursive=False):
        """
        Add child STAC Collections to overall STAC Catalog
        """
        if self.children:
            return self.children

        # create dask bag to coordinate multi processing
        bag = db.from_sequence(v for v in self.obj.values())
        root_bag = db.from_sequence(self.catalog for v in self.obj.values())

        children: db.Bag = bag.map(MetaCollection)
        cols = children.map(MetaCollection.get_stac)
        add_root= cols.map(lambda col, root: col.set_root(root.catalog), root_bag)
        save_col = cols.map(lambda col, root, rooted: col.normalize_and_save(root.get_href()), root_bag, add_root)
        save_col.compute()

        self.catalog.add_children(children)
        self.catalog.normalize_hrefs(root_href=self.dst)

        return self.children

    def get_stac(self):
        """
        Return overall STAC Catalog
        """
        return self.catalog

class PCParser(HTMLParser):
    """
    Parser HTML returned from rockyweb endpoints, finding laz files associated
    with a specific project. These laz files also share names (minus suffix) with
    the metadata files, which are located in the metadata directory up a level.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.messages = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        attrs_json = dict(attrs)
        if tag == 'a':
            for k,v in attrs_json.items():
                if k == 'href' and '.laz' in v:
                    self.messages.append(v)

class MetaCollection:
    """
    MetaCollection will read the corresponding JSON section, pull relevant info from
    it, and create a list of MetaItems from the directory of laz files found at the
    pointcloud path found in the JSON.
    """

    def __init__(self, obj):
        self.meta = WesmMetadata(**obj)
        self.pc_dir = urljoin(self.meta.lpc_link, 'LAZ/')
        self.sidecar_dir = urljoin(self.meta.lpc_link, 'metadata/')

        e = pystac.Extent(
            spatial=pystac.SpatialExtent(bboxes=self.meta.bbox),
            temporal=pystac.TemporalExtent(intervals=[
                datetime.fromisoformat(self.meta.collect_start),
                datetime.fromisoformat(self.meta.collect_end)
            ])
        )
        self.collection = pystac.Collection(
            id=self.meta.FESMProjectID,
            description='STAC Collection for USGS Project'
                f'{self.meta.FESMProjectID} derived from WESM JSON.',
            extent=e,
        )
        self.pc_paths = None
        self.sidecar_paths = None

    def set_paths(self):
        # grab pointcloud paths and sidecar paths
        parser = PCParser()
        res = requests.get(self.pc_dir)
        parser.feed(res.text)
        self.pc_paths = [urljoin(self.pc_dir, p) for p in parser.messages]

        meta_messages = [m.replace('.laz', '.xml') for m in parser.messages]
        self.sidecar_paths = [
            urljoin(self.sidecar_dir, m) for m in meta_messages
        ]

    def set_children(self) -> None:
        """
        Add children to the project STAC Collection
        """
        if not self.pc_paths or not self.sidecar_paths:
            self.set_paths()

        vars = zip(self.pc_paths, self.sidecar_paths)

        logger.info(f'{self.meta.FESMProjectID}')
        item_bag = db.from_sequence(vars).map(
            lambda x: MetaItem(x[0],x[1],self.meta).get_stac())
        self.items = item_bag.persist()

        # with ProgressBar():
        self.collection.add_items(self.items)

    def get_stac(self, recursive=False) -> pystac.Collection:
        """
        Return project STAC Collection
        """
        if recursive:
            self.set_children()
        return self.collection

    @staticmethod
    def get_stac(c: Self, recursive=False):
        return c.get_stac(recursive)


    def __repr__(self):
        return json.dumps(self.meta)

class MetaItem:
    """
    MetaItem will run PDAL very coursely over this pointcloud, and create a STAC item
    from it. It will use the sidecar file found in the metadata directory to fill in
    any gaps in information.
    """

    def __init__(self, pc_path: str, meta_path: str, wesm_meta: WesmMetadata):
        self.pc_path = pc_path
        self.meta_path = meta_path
        self.meta = wesm_meta

    def info(self):
        cargs = ['pdal','info','--metadata', '--schema', str(self.pc_path)]
        p = subprocess.Popen(cargs, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    encoding='utf8')
        ret = p.communicate()
        if p.returncode != 0:
            error = ret[1]
            logger.error(cargs)
            logger.error(error)
            self.error = {"args":cargs, "error": error}
            raise AttributeError(error)
        self.stats = json.loads(ret[0])
        return self.stats

    def get_stac(self) -> pystac.Item:

        # determine if stac info needs to be re-run
        headers = requests.head(self.pc_path).headers
        if headers['ETag']:
            etag = headers['ETag']
            if '"' in etag:
                etag = etag.strip('"')
        else:
            etag = ''

        # run pdal info over laz data
        pdal_metadata = self.info()

        minx = pdal_metadata['metadata']["minx"]
        maxx = pdal_metadata['metadata']["maxx"]
        miny = pdal_metadata['metadata']["miny"]
        maxy = pdal_metadata['metadata']["maxy"]
        minz = pdal_metadata['metadata']["minz"]
        maxz = pdal_metadata['metadata']["maxz"]

        # transform data to 4326 for STAC, use source crs for projection extension
        src_crs_str = pdal_metadata['metadata']["spatialreference"]
        if src_crs_str:
            src_crs = pyproj.CRS.from_user_input(src_crs_str)
        else:
            # some data referenced by WESM doesn't have SRS info in it
            src_crs = pyproj.CRS.from_user_input(self.meta.horiz_crs)
        dst_crs = pyproj.CRS.from_epsg(4326)
        trn = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)

        left, bottom, right, top = trn.transform_bounds(
            minx, miny, maxx, maxy)
        bbox = [left, bottom, minz, right, top, maxz]

        shape = shapely.geometry.box(minx, miny, maxx, maxy)
        geometry = shapely.geometry.mapping(
            shapely.ops.transform(trn.transform, shape))

        # TODO figure out what other metadata should be going into the item
        # from the WESM JSON
        stac_id = Path(urlparse(self.pc_path).path).stem
        properties = {
            "start_datetime": self.meta.collect_start,
            "end_datetime": self.meta.collect_end,
            "seamless_category": self.meta.seamless_category,
            "etag": etag
        }

        item = pystac.Item(
            id=stac_id,
            # collection=self.meta.id,
            geometry=geometry,
            bbox=bbox,
            datetime=None,
            properties=properties,
        )

        #add pointcloud extension
        pointcloud: PointcloudExtension = PointcloudExtension.ext(item,
            add_if_missing=True)
        pointcloud.type = "lidar"
        pointcloud.schemas = [Schema(v) for v in
            pdal_metadata["schema"]["dimensions"]]
        pointcloud.count = pdal_metadata["metadata"]["count"]
        pointcloud.encoding = "application/vnd.laszip"

        # add projection extension
        projection: ProjectionExtension = ProjectionExtension.ext(item,
            add_if_missing=True)
        projection.epsg = None
        projection.projjson = src_crs.to_json_dict()
        projection.geometry = geometry
        # projection.geometry = hexbin_metadata["boundary_json"]
        projection.bbox = [minx, miny, minz, maxx, maxy, maxz]

        # add data and metadata asset
        item.add_asset(
            "data",
            pystac.Asset(
                title="LAS data",
                href=self.pc_path,
                roles=["data"],
                media_type="application/vnd.laszip",
            ),
        )
        item.add_asset(
            "metadata",
            pystac.Asset(
                title='Metadata',
                href=self.meta_path,
                roles=["metadata"],
                media_type="application/xml"))

        # add file extensions
        item.stac_extensions.append(
            "https://stac-extensions.github.io/file/v2.1.0/schema.json"
        )


        self.item = item
        return item