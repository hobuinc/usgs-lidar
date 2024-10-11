import json
from datetime import datetime

import multiprocessing
import subprocess
import logging
logger = logging.getLogger('usgs_boundary')
import requests
from urllib.parse import urljoin

import pyproj
from shapely.ops import transform

from shapely.geometry import mapping, MultiPolygon
import shapely.wkt
from shapely.ops import transform
import shapely.errors
from pyproj import CRS

from pystac import Link, Asset, Item
from pystac.extensions.projection import ProjectionExtension

from pystac.extensions.pointcloud import (
    PhenomenologyType,
    PointcloudExtension,
    Schema,
)

crs = CRS.from_epsg(3857)
PROJJSON = json.loads(crs.to_json())
transformation = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)

def run(task):
    task.run()
    return task

class Command(object):
    def __init__(self, args):
        self.args = args

    def __repr__(self):
        return f'{self.args}'

class Task(object):
    def __init__(self, bucket, key, resolution=1000, metadata=None):
        self.bucket = bucket
        self.key = key
        self.name = key.strip('/')
        self.url = f'https://s3-us-west-2.amazonaws.com/{self.bucket}/{self.key}ept.json'
        self.resolution = resolution
        self.metadata = metadata
        self.stats = None
        self.wkt = None
        self.error = None
        self.ept = None
        self.poly = None
        self.stac_item = None

    def geometry(self):
        self.wkt = self.stats['boundary']['boundary']

        try:
            self.poly = shapely.wkt.loads(self.wkt)
            if self.poly.geom_type == 'Polygon':
                self.poly = MultiPolygon([self.poly])
            self.poly = transform(transformation.transform, self.poly)
        except Exception as E:
            self.error = {"error": str(E)}
            print(f"failed to convert WKT for {self.key}", E)


    def run (self):
        try:
            self.count()
            self.info()
            self.geometry()
            self.stac()

        except (AttributeError, KeyError, json.decoder.JSONDecodeError,shapely.errors.WKTReadingError):
            logger.error(f'Failed to run task with key {self.key}')
            pass

    def count (self):
        try:
            self.ept = requests.get(self.url).json()
        except Exception as E:
            logger.error(E)
            self.error = {"tile":self.name, "error": str(E)}
            raise AttributeError(E)

        self.num_points = int(self.ept['points'])

    def info (self):
        cargs = ['pdal','info','--all',
                '--driver','readers.ept',
                f'--readers.ept.resolution={self.resolution}',
                f'--readers.ept.threads=6',
                f'--filters.hexbin.edge_size=1000',
                f'--filters.hexbin.threshold=1',
                self.url]
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

    def stac(self):
        from .metadata import MetaCollection
        if not self.poly:
            return None

        date_start = None
        date_end = None
        if self.metadata:
            m = self.metadata
            m = MetaCollection(self.metadata)
            date_start = m.meta.collect_start
            date_end = m.meta.collect_end
            # meta_asset = Asset(urljoin(m.meta.lpc_link, 'metadata/'),
            #     'metadata', roles=['metadata'])
            # set up the pointcloud paths and sidecar paths
            # grab sidecar paths and add as metadata assets
            m.set_paths()
            meta_assets= [
                Asset(title=f'metadata_{num}', href=meta_url, roles=['metadata'])
                for num, meta_url in enumerate(m.sidecar_paths)
            ]

        else:
            meta_assets= []
            date_start = datetime.now().isoformat()+'Z'
            date_end= datetime.now().isoformat()+'Z'


        item = Item(self.name,
                    mapping(self.poly),
                    list(self.poly.bounds),
                    None,
                    {
                        'description': f'USGS Lidar pointcloud {self.name} in Entwine/EPT format',
                        'start_datetime': date_start,
                        'end_datetime': date_end
                    })
        for meta_asset in meta_assets:
            item.add_asset(meta_asset.title, meta_asset)

        # icky
        s = self.ept['schema']
        p = []
        for d in s:
            # change 'float' to 'floating' to fit pointcloud stac schema
            if d['type'] == 'float':
                d['type'] = 'floating'
            p.append(Schema(d))


        PointcloudExtension.add_to(item)
        PointcloudExtension.ext(item).apply(
            self.num_points,
            PhenomenologyType.LIDAR,
            "ept",
            p,
        )

        ProjectionExtension.add_to(item)
        ProjectionExtension.ext(item).apply(
            3857,
            projjson=PROJJSON
        )

        asset = Asset(self.url, 'entwine', 'The ept.json for accessing data')
        item.add_asset('ept.json', asset)

        self.stac_item = item


    def __repr__(self):
        return f'{self.bucket} {self.key}'

class Process(object):

    def __init__(self):
        self.tasks = []
        self.results = []

    def put(self, task):
        self.tasks.append(task)

    def do(self, count = multiprocessing.cpu_count()):
        pool = multiprocessing.Pool(processes=count)
        self.results = (pool.map(run, self.tasks))
#        import pdb;pdb.set_trace()

