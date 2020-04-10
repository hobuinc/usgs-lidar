import ogr
import osr
import glob
import json
import shutil
ogr.UseExceptions()

web_mercator = osr.SpatialReference()
web_mercator.ImportFromEPSG(3857)


geographic = osr.SpatialReference()
geographic.ImportFromEPSG(4326)

geographic.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);

jsonfiles = []
for f in glob.glob("source/*.json"):
    jsonfiles.append(f)

import os
try:
    os.mkdir('geojson')
except FileExistsError:
    shutil.rmtree('geojson')
    os.mkdir('geojson')



drv = ogr.GetDriverByName('GeoJSON')
ds = drv.CreateDataSource('resources.geojson')
lyr = ds.CreateLayer("resources", geom_type=ogr.wkbMultiPolygon, options=["RFC7946=YES"])

urlField = ogr.FieldDefn("url", ogr.OFTString)
lyr.CreateField(urlField)
idField = ogr.FieldDefn("id", ogr.OFTInteger)
lyr.CreateField(idField)

featureDefn = lyr.GetLayerDefn()

base_url = 'https://s3-us-west-2.amazonaws.com/usgs-lidar-public'
i = 0
def process(f):
    global i
    with open(f) as j:
        data = j.read()

    basename = os.path.basename(f)
    url = base_url +'/'+ basename.split('.')[0] + '/ept.json'
    j = json.loads(data)
    wkt = j['stages']['filters.hexbin']['boundary']
    g = ogr.CreateGeometryFromWkt(wkt)
    g.AssignSpatialReference(web_mercator)
    g.TransformTo(geographic)
    geojson = g.ExportToJson()

    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(g)
    feature.SetField("url", url)
    feature.SetField("id", i)
    lyr.CreateFeature(feature)

    feature = None
    i += 1

    output = os.path.join('geojson', os.path.basename(f))
    with open(output,'wb') as j:
        j.write(geojson.encode('utf-8'))

for f in jsonfiles:
    process (f)
