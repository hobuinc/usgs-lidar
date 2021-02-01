
import fiona
from shapely.geometry import mapping, Polygon, MultiPolygon
from shapely.wkt import loads
from collections import OrderedDict
import pyproj
from shapely.ops import transform

import pystac
import requests
import datetime

schema = {
   'geometry': 'MultiPolygon',
   'properties': OrderedDict([
     ('name', 'str'),
     ('id', 'int'),
     ('count', 'int64'),
     ('url', 'str')
   ])
 }


from pystac.extensions.pointcloud import PointcloudSchema

transformation = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)

# Will be written when self.layer.__del__ is called
class Layer(object):
    def __init__(self, args):
        self.args = args
        self.count = 0

        self.initialize()

    def initialize(self):

        output_driver = "GeoJSON"
        self.layer = fiona.open(
                 self.args.layer,
                 'w',
                 driver=output_driver,
                 schema=schema)

    def add_stac(self, tile):

        if not tile.poly:
            return None

        item = pystac.Item(tile.name,
                           mapping(tile.poly),
                           list(tile.poly.bounds),
                           datetime.datetime.now(),
                           {'description': 'A USGS Lidar pointcloud in Entwine/EPT format'})

        item.ext.enable(pystac.Extensions.POINTCLOUD)

        # icky
        s = tile.ept['schema']
        p = []
        for d in s:
            p.append(pystac.extensions.pointcloud.PointcloudSchema(d))

        item.ext.pointcloud.apply(tile.num_points, 'lidar', 'ept', p, epsg='EPSG:3857')

        asset = pystac.Asset(tile.url, 'entwine', 'The ept.json for accessing data')
        item.add_asset('ept.json', asset)

        item_link = pystac.Link('self', f'{self.args.stac_base_url}{tile.name}.json')
        item_parent = pystac.Link('parent', f'{self.args.stac_base_url}catalog.json')
        item.add_links([item_link, item_parent])
        return item

    def add(self, tile):
        if not tile.wkt:
            # log this bad tile ID somewhere
            return

        feature =  {
            'geometry': mapping(tile.poly),
            'properties': OrderedDict([
             ('name', tile.name),
             ('id', self.count),
             ('count', tile.num_points),
             ('url', tile.url)
            ])
         }

        self.layer.write(feature)

        self.count += 1



