
import fiona
from shapely.geometry import mapping, Polygon, MultiPolygon
from shapely.wkt import loads
from collections import OrderedDict


schema = {
   'geometry': 'MultiPolygon',
   'properties': OrderedDict([
     ('name', 'str'),
     ('id', 'int'),
     ('url', 'str')
   ])
 }


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

    def add(self, tile):
        if not tile.wkt:
            # log this bad tile ID somewhere
            return
        poly = loads(tile.wkt)

        if poly.type == 'Polygon':
            poly = MultiPolygon([poly])
        feature =  {
            'geometry': mapping(poly),
            'properties': OrderedDict([
             ('name', 'something'),
             ('id', self.count),
             ('url', tile.url)
            ])
         }

        self.layer.write(feature)

        self.count += 1




