
import fiona
from shapely.geometry import mapping, Polygon, MultiPolygon
from shapely.wkt import loads
from collections import OrderedDict
import pyproj
from shapely.ops import transform

schema = {
   'geometry': 'MultiPolygon',
   'properties': OrderedDict([
     ('name', 'str'),
     ('id', 'int'),
     ('url', 'str')
   ])
 }



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

    def add(self, tile):
        if not tile.wkt:
            # log this bad tile ID somewhere
            return
        poly = loads(tile.wkt)

        if poly.type == 'Polygon':
            poly = MultiPolygon([poly])
        poly = transform(transformation.transform, poly)
        feature =  {
            'geometry': mapping(poly),
            'properties': OrderedDict([
             ('name', tile.key.strip('/')),
             ('id', self.count),
             ('url', tile.url)
            ])
         }

        self.layer.write(feature)

        self.count += 1




