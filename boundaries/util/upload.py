import ogr
import osr
import glob
import json
import shutil
import boto3

session = boto3.session.Session(profile_name='stor')

s3 = session.client('s3')



jsonfiles = []
for f in glob.glob("geojson/*.json"):
    jsonfiles.append(f)




def process(f):
    key = f.split('/')[1].split('.')[0] +'/boundary.json'
    print (key)
    with open(f, 'rb') as j:
        data = j.read()
        s3.upload_file(f, 'usgs-lidar-public', key)

#process (jsonfiles[0])
for f in jsonfiles:
    process (f)
