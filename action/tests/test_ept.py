import pytest
import shapely

from usgs_boundary.proqueue import Task

@pytest.fixture
def task_ept():
    yield {
        'bounds': [-12299794, 5649790, 2325, -12298360, 5651224, 3759],
        'boundsConforming': [-12299791.0, 5649791.0, 2852.0, -12298364.0,
            5651223.0, 3232.0],
        'dataType': 'laszip',
        'hierarchyType': 'json',
        'points': 5306053,
        'schema': [
            {'name': 'X', 'offset': -12299077, 'scale': 0.01, 'size': 4, 'type': 'signed'},
            {'name': 'Y', 'offset': 5650507, 'scale': 0.01, 'size': 4, 'type': 'signed'},
            {'name': 'Z', 'offset': 3042, 'scale': 0.01, 'size': 4, 'type': 'signed'},
            {'name': 'Intensity', 'size': 2, 'type': 'unsigned'},
            {'name': 'ReturnNumber', 'size': 1, 'type': 'unsigned'},
            {'name': 'NumberOfReturns', 'size': 1, 'type': 'unsigned'},
            {'name': 'ScanDirectionFlag', 'size': 1, 'type': 'unsigned'},
            {'name': 'EdgeOfFlightLine', 'size': 1, 'type': 'unsigned'},
            {'name': 'Classification', 'size': 1, 'type': 'unsigned'},
            {'name': 'ScanAngleRank', 'size': 4, 'type': 'floating'},
            {'name': 'UserData', 'size': 1, 'type': 'unsigned'},
            {'name': 'PointSourceId', 'size': 2, 'type': 'unsigned'},
            {'name': 'GpsTime', 'size': 8, 'type': 'floating'},
            {'name': 'ScanChannel', 'size': 1, 'type': 'unsigned'},
            {'name': 'ClassFlags', 'size': 1, 'type': 'unsigned'}
        ],
        'span': 128,
        'srs': {
            'authority': 'EPSG',
            'horizontal': '3857',
            'wkt': 'PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]'},
        'version': '1.0.0'
    }

@pytest.fixture
def polygon():
    yield shapely.from_wkt('MULTIPOLYGON (((-110.48183846654055 45.165767834035904, -110.46387216085816 45.18770398507912, -110.49082161938175 45.19866920820327, -110.50878792506414 45.18770398507912, -110.48183846654055 45.165767834035904)))')

@pytest.fixture
def point_count():
    yield 5306053

def test_task(meta_json, task_ept, polygon, point_count):

    task = Task(bucket='usgs-lidar-public',
        key='WY_YellowstoneNP_1RF_2020/',
        resolution=1000,
        metadata=meta_json)

    task.count()
    task.info()
    task.geometry()
    task.stac()

    assert task.poly == polygon
    assert task.stac_item.validate()
    assert task.stac_item.to_dict()
    assert task.ept == task_ept
    assert task.num_points == point_count