import sys
import io
import json
import pyproj
import datetime
from os import path, makedirs

import xml.etree.ElementTree as ET

from urllib import request
from typing import List

from pystac import ItemCollection, Item, Link, Asset
from pystac.extensions.pointcloud import PointcloudExtension, Schema
from pystac.extensions.projection import ProjectionExtension

from shapely.ops import transform
from shapely.geometry import shape, mapping

def get_json_info(href):
    try:
        contents = request.urlopen(href).read()
    except:
        return {}
    json_info = json.loads(contents)
    return json_info

def parse_metadata(href):
    metadata_info = {}
    metadata_path = path.join(href, 'inport-xml')
    try:
        contents = request.urlopen(metadata_path).read()
    except:
        return metadata_info
    parsed = ET.fromstring(contents)

    # Get data description
    description = parsed.find('item-identification').find('abstract').text
    if description:
        metadata_info['description'] = description

    # Find dates. Start with start and end dates if range, start date if discrete
    # If those don't exist, get publication date. If that doesn't exist, return nothing
    # and we'll attempt dates from the feature data
    extents = parsed.find('extents').find('extent')
    try:
        dates = extents.find('time-frames').find('time-frame')
        date_type = dates.find('time-frame-type').text
        if date_type == 'Range':
            metadata_info['start_date'] = dates.find('start-date-time').text
            metadata_info['end_date'] = dates.find('end-date-time').text
        elif date_type == 'Discrete':
            metadata_info['date'] = dates.find('start-date-time').text
    except AttributeError:
        if parsed.find('item-identification').find('publication-date'):
            metadata_info['date'] = parsed.find('item-identification').find('publication-date').text

    # Get support links. If there are no contact links, return nothing.
    support_roles = parsed.find('support-roles')
    if support_roles:
        metadata_info['support_roles'] = []
        for sr in support_roles:
            try:
                metadata_info['support_roles'].append(
                    {
                        'rel': sr.find('contact-url').text,
                        'title': sr.find('support-role-type').text
                    }
                )
            except AttributeError:
                pass

    return metadata_info

def make_datetime(date_string):
    if len(date_string)== 4:
        return datetime.datetime.strptime(date_string, '%Y')
    elif len(date_string) == 7:
        return datetime.datetime.strptime(date_string, '%Y-%m')
    else:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d')

def make_datetime_str(date_string):
    return make_datetime(date_string).isoformat() + "Z"


def process_one(feature, src_crs, dst_crs, trn):
    properties = feature['properties']
    name = properties['Name']

    src_geometry = feature['geometry']
    s = shape(src_geometry)
    src_bbox = list(s.bounds)

    item_bbox = trn.transform_bounds(*src_bbox)
    item_geometry = mapping(transform(trn.transform, s))

    metadata_link = properties['Metalink']
    metadata = parse_metadata(metadata_link)
    item_properties = { 'description': metadata['description'] }

    # If start and end date are available, use them. If not go to discrete date.
    # If that's not there, use the date provided in the
    if 'start_date' in metadata and 'end_date' in metadata:
        item_properties['end_datetime'] = make_datetime_str(metadata['end_date'])
        item_properties['start_datetime'] = make_datetime_str(metadata['start_date'])
        item_date = None
    elif 'date' in metadata:
        item_date = make_datetime(metadata['date'])
    else:
        item_year = properties['Year']
        if item_year != 0:
            item_date = make_datetime(str(item_year))
        if item_year == 0:
            item_date = datetime.datetime.now()

    extra_links = properties['ExternalProviderLink']['links']
    ept_data = {}

    # Look for data links
    for link in extra_links:
        # skip invalid links
        if 'label' not in link and 'altlabel' not in link:
            continue
        if 'link' not in link:
            continue

        # Grab EPT data if it's available
        if link['label'] == 'EPT NOAA' or link['altlabel'] == 'Entwine Point Tile JSON file':
            ept_link = link['link']
            ept_data = get_json_info(ept_link)


    if not ept_data:
        print(f'Missing data for {name}')
        return { }

    # construct initial item
    item = Item(
        id=name,
        geometry=item_geometry,
        bbox=item_bbox,
        datetime=item_date,
        properties=item_properties
    )

    # Create pointcloud extension and required keys
    item_point_count = ept_data['points']
    ept_schema = ept_data['schema']
    item_schema = []
    for d in ept_schema:
        # change 'float' to 'floating' to fit pointcloud stac schema
        if d['type'] == 'float':
            d['type'] = 'floating'
        item_schema.append(Schema(d))

    PointcloudExtension.ext(item, add_if_missing=True).apply(
        encoding='ept',
        count=item_point_count,
        type='lidar',
        schemas=item_schema
    )

    # Create projection extension and required keys
    epsg = src_crs.to_epsg()
    ProjectionExtension.ext(item, add_if_missing=True).apply(
        epsg = epsg,
        geometry = src_geometry,
        projjson = src_crs.to_json_dict(),
        wkt2 = src_crs.to_wkt(),
        bbox = src_bbox,
    )
    asset = Asset(
        href=ept_link,
        title='EPT',
        media_type='application/json',
        roles=['data']
    )
    item.add_asset('ept', asset)
    return item


def noaa_info():
    noaa_url = f'https://noaa-nos-coastal-lidar-pds.s3.us-east-1.amazonaws.com/laz/dav.json'

    resources = get_json_info(noaa_url)
    src_crs = pyproj.CRS.from_user_input(resources['crs']['properties']['name'])
    dst_crs = pyproj.CRS.from_epsg(4326)
    trn = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)

    item_list: List[Item] = [ ]

    for feature in resources['features']:
        data_type = feature['properties']['DataType']

        # Only currently handling lidar data type
        if data_type == 'Lidar':
            item = process_one(feature, src_crs, dst_crs, trn)
        if item:
            item_list.append(item)

    return ItemCollection(item_list)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compute boundaries for USGS 3DEP EPT PDS")
    parser.add_argument("--stac_directory", default="stac_ept", type=str, help="Directory to put stac catalog")
    parser.add_argument("--stac_bucket", type=str, help="Bucket to output STAC info", default="usgs-lidar-stac")
    parser.add_argument("--region", type=str, default="us-west-2", help="AWS region")


    args = parser.parse_args()

    stac_output_url = f'https://s3-{args.region}.amazonaws.com/{args.stac_bucket}/noaa/'

    item_collection = noaa_info()
    if args.stac_directory:
        if not path.exists(args.stac_directory):
            makedirs(args.stac_directory)
        with open(path.join(args.stac_directory, 'noaa_item_collection.json'), 'w') as out_file:
            print("Writing out to ", path.join(args.stac_directory, 'noaa_item_collection.json'))
            out_file.write(json.dumps(item_collection.to_dict()))


main()