import os
import logging

# set up logger for CloudWatch
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

import subprocess
import json

# invoke 'pdal info https://pdal.io/apps/info.html for a cloud-readable
# datasource. This can be an S3-accessible file or an EPT URL with a bounds.
def pdal_info(event, context):
    """ pdal info lambda handler """

    # GDAL_DATA is needed by GDAL for any reprojection
    # or coordinate system operations.
    os.environ['GDAL_DATA'] = '/opt/share/gdal'
    os.environ['HOME'] = '/tmp'

    # event is a dictionary of items passed to us
    # if no 'action' was specified in the JSON, we'll
    # simply call `pdal info --all`
    if 'action' not in event:
        event['action'] = 'all'

    # All Lambda Layer content is dumped into /opt
    args = ['/opt/bin/pdal', 'info', '--'+event.pop('action'), event.pop('filename')]

    # For each key/value in the JSON that isn't
    # action or filename, set the driver-based options as necessary
    for key in event:
        args.append('--'+key+'='+event[key])

    # Invoke pdal info
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.communicate()

    # If pdal info returns an error code, return
    # that to the user, otherwise, set it as the body
    # and return
    if p.returncode != 0:
        error = ret[1]
        return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': {'error': error }
                }

    j = ret[0]
    j = json.loads(j)
    return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': j
            }




def pdal_translate(event, context):
    """ pdal translate lambda handler """

    # GDAL_DATA is needed by GDAL for any reprojection
    # or coordinate system operations.
    os.environ['GDAL_DATA'] = '/opt/share/gdal'
    os.environ['HOME'] = '/tmp'

    # event is a dictionary of items passed to us
    # if no 'action' was specified in the JSON, we'll
    # simply call `pdal info --all`
    if 'action' not in event:
        event['action'] = 'all'

    # All Lambda Layer content is dumped into /opt
    args = ['/opt/bin/pdal', 'info', '--'+event.pop('action'), event.pop('filename')]

    # For each key/value in the JSON that isn't
    # action or filename, set the driver-based options as necessary
    for key in event:
        args.append('--'+key+'='+event[key])

    # Invoke pdal info
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.communicate()

    # If pdal info returns an error code, return
    # that to the user, otherwise, set it as the body
    # and return
    if p.returncode != 0:
        error = ret[1]
        return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': {'error': error }
                }

    j = ret[0]
    j = json.loads(j)
    return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': j
            }

def pdal_pipeline(event, context):
    """ pdal pipeline lambda handler """

    import json
    import base64
    # GDAL_DATA is needed by GDAL for any reprojection
    # or coordinate system operations.
    os.environ['GDAL_DATA'] = '/opt/share/gdal'
    os.environ['HOME'] = '/tmp'

    # All Lambda Layer content is dumped into /opt
    args = ['/opt/bin/pdal', 'pipeline', '--stdin', '--pipeline-serialization', 'STDOUT']
#    pipeline = json.loads(event['body'])
    try:

        j =base64.b64decode(event['body']).decode('utf-8')
        pipeline = json.loads(j)
    except:
        pipeline = event
    logger.debug(pipeline)

#
#     return {
#             'statusCode': 200,
#             'headers': {'Content-Type': 'application/json'},
#             'isBase64Encoded':False,
#             'body': 'hello' #json.dumps(b64)
#             }
    # Invoke pdal info
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf8')
    ret = p.communicate(input=json.dumps(pipeline))

    # If pdal pipeline returns an error code, return
    # that to the user, otherwise, set it as the body
    # and return
    if p.returncode != 0:
        error = ret[1]
        return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': error })
                }

    j = ret[0]
    pipeline = json.loads(j)

    args = ['/opt/bin/gdaldem', 'hillshade', '/tmp/dtm.tif','/tmp/hillshade.tif']
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.communicate()
    if p.returncode != 0:
        error = ret[1]
        return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': error })
                }
    args = ['/opt/bin/gdal_translate', '/tmp/hillshade.tif','/tmp/hillshade.png']
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.communicate()
    if p.returncode != 0:
        error = ret[1]
        return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': error })
                }

    import base64

    with open('/tmp/hillshade.png', "rb") as image_file:
        b64 = base64.b64encode(image_file.read()).decode('utf-8')

        return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'isBase64Encoded':True,
                'body': b64
                }

