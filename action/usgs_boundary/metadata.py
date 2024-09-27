import json
import logging

from datetime import datetime
from typing import Any

import requests
from html.parser import HTMLParser
from urllib.parse import urljoin

import subprocess
import dask.bag as db
import pystac
import pyproj
import shapely.wkt
import shapely
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.pointcloud import PointcloudExtension

from .info import read_json

logger = logging.getLogger('wesm_stac')

class MetaCatalog:
    """
    MetaCatalog reads the WESM JSON file at the given url, and creates a list of
    MetaCollections. Dask Bag helps facilitate the mapping of this in parallel.
    """
    def __init__(self, url: str) -> None:
        self.url = url
        self.children = None
        self.catalog = None

    def create_collections(self):
        obj: dict = read_json(self.url)
        bag = db.from_sequence(v for v in obj.values())
        self.children: db.Bag = bag.map(MetaCollection).map(
            lambda col: col.get_stac())

        return self.children

    def get_stac(self):
        if self.children is None:
            self.create_collections()

        return pystac.Catalog(id='WESM Catalog', description='Catalog representing'
        ' WESM metadata and associated point cloud files.')

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
        self.meta = obj
        self.id = self.meta['FESMProjectID']
        self.hcrs = self.meta['horiz_crs']
        self.vcrs = self.meta['vert_crs']

        self.meta_link = self.meta['metadata_link']
        self.collect_start = self.meta['collect_start']
        self.collect_end = self.meta['collect_end']
        self.bbox = self.meta['bbox']
        if self.bbox:
            str_box = self.bbox.strip(' ').split(',')
            self.bbox = [float(v) for v in str_box]

        # this link is a directory, and needs trailing slash to show that in urljoin
        lpc_link = self.meta['lpc_link']
        if lpc_link[:-1] != '/':
            lpc_link = lpc_link + '/'

        self.pc_dir = urljoin(lpc_link, 'LAZ/')
        self.sidecar_dir = urljoin(lpc_link, 'metadata/')


    def set_pc_paths(self) -> list[str]:
        """
        Using the pointcloud path from the metadata, search for all the point
        cloud tiles that are available and store them along with their
        sidecar metadata file paths for creating STAC Items.
        """
        parser = PCParser()
        res = requests.get(self.pc_dir)
        parser.feed(res.text)
        self.pc_paths = [urljoin(self.pc_dir, p) for p in parser.messages]

        meta_messages = [m.replace('.laz', '.xml') for m in parser.messages]
        self.sidecar_paths = [
            urljoin(self.sidecar_dir, m) for m in meta_messages
        ]

    def get_stac(self) -> pystac.Collection:
        """
        Create STAC Collection as well as all child STAC Items
        """
        e = pystac.Extent()
        # db.from_sequence(self.pc_paths).map(MetaItem).map(lambda mi: mi.get_stac())
        return pystac.Collection(id=self.id, description='', extent='# TODO')

    def __repr__(self):
        return json.dumps(self.meta)

class MetaItem:
    """
    MetaItem will run PDAL very coursely over this pointcloud, and create a STAC item
    from it. It will use the sidecar file found in the metadata directory to fill in
    any gaps in information.
    """

    def __init__(self, pc_path: str, meta_path: str, col_meta: MetaCollection):
        self.pc_path = pc_path
        self.meta_path = meta_path
        self.col_meta = col_meta

    def info(self):

        cargs = ['pdal','info','--all',
                f'--filters.hexbin.edge_size=1000',
                f'--filters.hexbin.threshold=1',
                str(self.pc_path)]
        logger.debug(" ".join(cargs))
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

        # run pdal info over laz data
        pdal_metadata = self.info()

        pdal_bbox = pdal_metadata['stats']['bbox']['native']['bbox']
        minx = pdal_bbox["minx"]
        maxx = pdal_bbox["maxx"]
        miny = pdal_bbox["miny"]
        maxy = pdal_bbox["maxy"]
        minz = pdal_bbox["minz"]
        maxz = pdal_bbox["maxz"]

        # transform data to 4326 for STAC, use source crs for projection extension
        try:
            src_crs = pyproj.CRS.from_user_input(pdal_metadata['metadata']["spatialreference"])
        except KeyError:
            # some data referenced by WESM doesn't have SRS info in it
            src_crs = pyproj.CRS.from_user_input(self.col_meta.hcrs)
        dst_crs = pyproj.CRS.from_epsg(4326)
        trn = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)

        left, bottom, right, top = trn.transform_bounds(minx, miny, maxx, maxy)
        bbox = [left, bottom, minz, right, top, maxz]

        hexbin_metadata = pdal_metadata["boundary"]
        shape = shapely.geometry.shape(hexbin_metadata["boundary_json"])
        geometry = shapely.geometry.mapping(shapely.ops.transform(trn.transform, shape))

        # TODO figure out what other metadata should be going into the item
        # from the WESM JSON
        item = pystac.Item(
            id=self.meta['id'],
            geometry=geometry,
            bbox=bbox,
            datetime=None,
            properties={
                "start_datetime": self.col_meta.collect_start,
                "end_datetime": self.col_meta.collect_end,
            },
        )

        #add pointcloud extension
        pointcloud = PointcloudExtension.ext(item, add_if_missing=True)
        pointcloud.type = "lidar"
        pointcloud.schemas = pdal_metadata["schema"]["dimensions"]
        pointcloud.count = pdal_metadata["count"]
        pointcloud.encoding = "application/vnd.laszip"
        pointcloud.density = hexbin_metadata['avg_pt_per_sq_unit']
        pointcloud.statistics = pdal_metadata['stats']['statistic']


        # add projection extension
        projection = ProjectionExtension.ext(item, add_if_missing=True)
        projection.epsg = None
        projection.projjson = src_crs.to_json_dict()
        projection.geometry = hexbin_metadata["boundary_json"]
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

        item.validate()
        self.item = item
        return item