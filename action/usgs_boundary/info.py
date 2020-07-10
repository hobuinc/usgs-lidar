

import sys
import io
import json
from .proqueue import Process, Task, Command

from .layer import Layer

import boto3


import logging
logger = logging.getLogger('usgs_boundary')


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

    count = 0
    for k in keys:

        if count == args.limit and count != 0:
            break

        t = Task(args.bucket, k, args.resolution)
        queue.put(t)

        logger.debug(t)

        count += 1

    queue.do(count=20)

    l = Layer(args)
    for r in queue.results:
        l.add(r)


    errors = []
    for r in queue.results:
        if r.error:
            errors.append(r.error)

    f = open('errors.json','wb')
    f.write(json.dumps(errors).encode('utf-8'))
    f.close()






