import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import pyproj

from usgs_boundary import noaa


GEOMETRY = {
    'type': 'Polygon',
    'coordinates': [[[-90, 30], [-89, 30], [-89, 31], [-90, 31], [-90, 30]]],
}


def inventory_page(mission_id, total=2):
    return {
        'missionCount': total,
        'missions': {
            'data': [{
                'missionId': mission_id,
                'title': f'Lidar survey {mission_id}',
                'dataType': 'Lidar',
                'attributes': {
                    'year': '2020',
                    'links': [
                        {'title': 'Metadata', 'linkTypeName': 'Metadata',
                         'uri': 'https://example.com/metadata'},
                        {'title': 'EPT NOAA', 'linkTypeName': 'EPT JSON',
                         'uri': 'https://example.com/ept.json'},
                    ],
                },
            }],
            'geoJson': {'features': [{
                'properties': {'missionId': mission_id},
                'geometry': GEOMETRY,
            }]},
        },
    }


class NOAAInventoryTests(unittest.TestCase):
    def test_pagination_preserves_geometry_and_metadata_links(self):
        pages = [inventory_page(41), inventory_page(9079)]
        with patch.object(noaa.request, 'urlopen', side_effect=[
            io.BytesIO(json.dumps(page).encode()) for page in pages
        ]) as urlopen:
            resources = noaa.get_resources()
        self.assertEqual(len(resources['features']), 2)
        self.assertEqual(resources['crs']['properties']['name'], 'EPSG:4326')
        first, second = resources['features']
        self.assertEqual(first['geometry'], GEOMETRY)
        self.assertEqual(second['properties']['Name'], 'Lidar survey 9079')
        self.assertEqual(first['properties']['Metalink'], 'https://example.com/metadata')
        self.assertEqual(first['properties']['ExternalProviderLink']['links'][1], {
            'label': 'EPT NOAA', 'link': 'https://example.com/ept.json',
        })
        queries = [json.loads(call.args[0].data) for call in urlopen.call_args_list]
        self.assertEqual([query['page'] for query in queries], [0, 1])
        self.assertTrue(all(query['published'] == 'true' for query in queries))
        # An empty missionIds filter makes the API return no missions.
        self.assertTrue(all('missionIds' not in query for query in queries))

    def test_empty_inventory_fails(self):
        page = {'missionCount': 0, 'missions': {'data': []}}
        with patch.object(noaa.request, 'urlopen', return_value=io.BytesIO(json.dumps(page).encode())):
            with self.assertRaisesRegex(RuntimeError, 'empty page'):
                noaa.get_resources()

    def test_inventory_http_failure_is_not_an_empty_catalog(self):
        error = HTTPError('https://example.com/inventory', 404, 'Not Found', {}, None)
        with patch.object(noaa.request, 'urlopen', side_effect=error):
            with self.assertRaises(HTTPError):
                noaa.get_resources()

    def test_ept_link_without_altlabel_and_missing_optional_metadata(self):
        feature = {
            'geometry': GEOMETRY,
            'properties': {
                'Name': 'Example lidar',
                'Year': '2020',
                'Metalink': '',
                'ExternalProviderLink': {'links': [
                    {'label': 'Metadata', 'link': 'https://example.com/metadata'},
                    {'label': 'EPT NOAA', 'link': 'https://example.com/ept.json'},
                ]},
            },
        }
        ept = {'points': 100, 'schema': [
            {'name': axis, 'type': 'signed', 'size': 4} for axis in ['X', 'Y', 'Z']
        ]}
        crs = pyproj.CRS.from_epsg(4326)
        transform = pyproj.Transformer.from_crs(crs, crs, always_xy=True)
        with patch.object(noaa, 'parse_metadata', return_value={}):
            with patch.object(noaa, 'get_json_info', return_value=ept) as fetch:
                item = noaa.process_one(feature, crs, crs, transform)
        fetch.assert_called_once_with('https://example.com/ept.json')
        self.assertEqual(item.properties['description'], 'Example lidar')
        self.assertEqual(item.properties['pc:count'], 100)
        self.assertEqual(item.datetime.year, 2020)
        self.assertEqual(item.assets['ept'].href, 'https://example.com/ept.json')


if __name__ == '__main__':
    unittest.main()
