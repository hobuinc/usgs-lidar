import fiona
from shapely.geometry import mapping, Polygon, MultiPolygon
from collections import OrderedDict

schema = {
   'geometry': 'MultiPolygon',
   'properties': OrderedDict([
     ('name', 'str'),
     ('id', 'int'),
     ('count', 'int64'),
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



