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
        self.url = f'https://s3-us-west-2.amazonaws.com/{self.bucket}/{self.key}ept.json'
        self.resolution = resolution
        self.stats = None
        self.wkt = None
        self.error = None

    def geometry(self):
        self.wkt = self.stats['boundary']['boundary']


    def run (self):
        try:
            self.info()
            self.geometry()
        except AttributeError:
            pass


    def info (self):
        cargs = ['pdal','info','--all',
                '--driver','readers.ept',
                f'--readers.ept.resolution={self.resolution}',
                f'--readers.ept.threads=6',
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

