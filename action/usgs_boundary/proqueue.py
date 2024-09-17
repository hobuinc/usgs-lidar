import boto3
import time
import os
import json

import multiprocessing
import subprocess
import string
from pathlib import Path
import logging
logger = logging.getLogger('usgs_boundary')
import requests

import pyproj

from shapely.geometry import mapping, Polygon, MultiPolygon
from shapely.wkt import loads
from shapely.ops import transform
import shapely.errors



from pathlib import Path



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
    def __init__(self, bucket, key, resolution=1000):
        self.bucket = bucket
        self.key = key
        self.name = key.strip('/')
        self.url = f'https://s3-us-west-2.amazonaws.com/{self.bucket}/{self.key}ept.json'
        self.resolution = resolution
        self.stats = None
        self.wkt = None
        self.error = None
        self.ept = None
        self.poly = None

    def geometry(self):
        self.wkt = self.stats['boundary']['boundary']

        try:
            self.poly = loads(self.wkt)
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

        except (AttributeError, KeyError, json.decoder.JSONDecodeError,shapely.errors.WKTReadingError):
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

