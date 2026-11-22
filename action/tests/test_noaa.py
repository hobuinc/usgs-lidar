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

    def test_reprojection_preserves_coordinates_and_dimensions(self):
        coordinates = [(0, 0), (111319.49079327357, 0),
                       (111319.49079327357, 111325.1428663851),
                       (0, 111325.1428663851), (0, 0)]
        expected = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
        source = pyproj.CRS.from_epsg(3857)
        destination = pyproj.CRS.from_epsg(4326)
        transformer = pyproj.Transformer.from_crs(source, destination, always_xy=True)
        for dimensions in (2, 3):
            with self.subTest(dimensions=dimensions):
                ring = [p if dimensions == 2 else (*p, 42) for p in coordinates]
                feature = {
                    'geometry': {'type': 'Polygon', 'coordinates': [ring]},
                    'properties': {
                        'Name': 'Projected lidar', 'Year': '2020', 'Metalink': '',
                        'ExternalProviderLink': {'links': [
                            {'label': 'EPT NOAA', 'link': 'https://example.com/ept.json'},
                        ]},
                    },
                }
                ept = {'points': 100, 'schema': [
                    {'name': axis, 'type': 'signed', 'size': 4} for axis in ['X', 'Y', 'Z']
                ]}
                with patch.object(noaa, 'parse_metadata', return_value={}):
                    with patch.object(noaa, 'get_json_info', return_value=ept):
                        item = noaa.process_one(feature, source, destination, transformer)
                ring = item.geometry['coordinates'][0]
                self.assertEqual(len(ring), len(expected))
                for actual, (longitude, latitude) in zip(ring, expected):
                    self.assertEqual(len(actual), dimensions)
                    self.assertAlmostEqual(actual[0], longitude)
                    self.assertAlmostEqual(actual[1], latitude)
                    if dimensions == 3:
                        self.assertEqual(actual[2], 42)


class NOAAMetadataTests(unittest.TestCase):
    def parse_xml(self, publication_date='', support_roles=''):
        xml = f'''<metadata>
            <item-identification><abstract>Example lidar</abstract>
                {publication_date}
            </item-identification>
            <extents><extent /></extents>
            {support_roles}
        </metadata>'''
        with patch.object(noaa.request, 'urlopen', return_value=io.BytesIO(xml.encode())):
            return noaa.parse_metadata('https://example.com/metadata')

    def test_publication_date_fallback_and_support_roles(self):
        metadata = self.parse_xml(
            '<publication-date>2020-05-06</publication-date>',
            '''<support-roles><support-role>
                <contact-url>https://example.com/provider</contact-url>
                <support-role-type>provider</support-role-type>
                <contact-name>Example provider</contact-name>
            </support-role></support-roles>''',
        )
        self.assertEqual(metadata['date'], '2020-05-06')
        self.assertEqual(metadata['support_roles'], [{
            'href': 'https://example.com/provider',
            'title': 'provider',
            'name': 'Example provider',
        }])

    def test_missing_or_empty_optional_elements(self):
        for date in ('', '<publication-date />'):
            for roles in ('', '<support-roles />'):
                with self.subTest(date=date, roles=roles):
                    metadata = self.parse_xml(date, roles)
                    self.assertEqual(metadata['description'], 'Example lidar')
                    self.assertNotIn('date', metadata)
                    self.assertEqual(metadata.get('support_roles', []), [])


if __name__ == '__main__':
    unittest.main()
