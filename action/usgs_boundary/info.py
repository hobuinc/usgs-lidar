

import sys
import io
import json
from .proqueue import Process, Task, Command

from .layer import Layer

import boto3


import logging
logger = logging.getLogger('usgs_boundary')

from pathlib import Path
import pystac

def read_json(filename, stdin=False):
    if stdin:
        buffer = sys.stdin.buffer
    else:
        buffer = open(filename, 'rb')

    stream = io.TextIOWrapper(buffer, encoding='utf-8')

    pipe = stream.read()
    pipe = json.loads(pipe)
    return pipe

def get_resources(bucket,
                  delimiter='',
                  prefix='',
                  suffix=''):

    s3 = boto3.client('s3')
    kwargs = {'Bucket': bucket}

    # If the prefix is a single string (not a tuple of strings), we can
    # do the filtering directly in the S3 API.
    if isinstance(prefix, str):
        kwargs['Prefix'] = prefix
    if isinstance(delimiter, str):
        kwargs['Delimiter'] = delimiter

    while True:

        # The S3 API response is a large blob of metadata.
        # 'Contents' contains information about the listed objects.
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp['CommonPrefixes']:
            key = obj['Prefix']
            yield key

        # The S3 API is paginated, returning up to 1000 keys at a time.
        # Pass the continuation token into the next response, until we
        # reach the final page (when this field is missing).
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


def info(args):

    keys = list(get_resources(args.bucket, delimiter='/'))
    logger.debug('Querying boundaries for %d keys' % (len(keys)))

    queue = Process()


    catalog = pystac.Catalog('3dep',
                         'A catalog of USGS 3DEP Lidar hosted on AWS s3.',
                         href=f'{args.stac_base_url}catalog.json',
                         stac_extensions=['POINTCLOUD'])

    base = Path(args.stac_directory)
    base.mkdir(exist_ok=True, parents=True)

    count = 0
    for k in keys:

        if count == args.limit and count != 0:
            break

        t = Task(args.bucket, k, args.resolution)
        queue.put(t)

#        logger.debug(t)

        count += 1

    queue.do(count=20)

    l = Layer(args)
    item_list = []
    for r in queue.results:
        if not r.error:

            l.add(r)

            with open(base / f"{r.name}.json", 'w') as f:
                i = l.add_stac(r)
                item_list.append(i)
                d = i.to_dict()
                json.dump(d, f)

            link = pystac.Link('item', f'{args.stac_base_url}{r.name}.json')
            catalog.add_link(link)
    item_collection = pystac.ItemCollection(items=item_list)

    errors = []
    for r in queue.results:
        if r.error:
            errors.append(r.error)

    f = open('errors.json','wb')
    f.write(json.dumps(errors).encode('utf-8'))
    f.close()


    with open(base / "catalog.json", 'w') as f:
        json.dump(catalog.to_dict(), f)

    with open(base / "item_collection.json", 'w') as f:
        json.dump(item_collection.to_dict(), f)
    # write item_collection.json






