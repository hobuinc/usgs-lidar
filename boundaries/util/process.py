import ogr
import osr
import glob
import json
import shutil


web_mercator = osr.SpatialReference()
web_mercator.ImportFromEPSG(3857)


geographic = osr.SpatialReference()
geographic.ImportFromEPSG(4326)


jsonfiles = []
for f in glob.glob("source/*.json"):
    jsonfiles.append(f)

import os
try:
    os.mkdir('geojson')
except FileExistsError:
    shutil.rmtree('geojson')
    os.mkdir('geojson')



def process(f):
    with open(f) as j:
        data = j.read()
    j = json.loads(data)
    wkt = j['stages']['filters.hexbin']['boundary']
    g = ogr.CreateGeometryFromWkt(wkt)
    g.AssignSpatialReference(web_mercator)
    g.TransformTo(geographic)
    geojson = g.ExportToJson()

    output = os.path.join('geojson', os.path.basename(f))
    with open(output,'wb') as j:
        j.write(geojson.encode('utf-8'))

for f in jsonfiles:
    process (f)
