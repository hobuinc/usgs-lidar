import json
import pyproj
import datetime
import xml.etree.ElementTree as ET

from os import path, makedirs
from urllib import request
from typing import List

from pystac import ItemCollection, Item, Link, Asset, Catalog, CatalogType, RelType
from pystac.extensions.pointcloud import PointcloudExtension, Schema
from pystac.extensions.projection import ProjectionExtension

from shapely.ops import transform
from shapely.geometry import shape, mapping

def get_json_info(href: str):
    try:
        contents = request.urlopen(href).read()
    except:
        return {}
    json_info = json.loads(contents)
    return json_info

def parse_metadata(href: str):
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
                        'href': sr.find('contact-url').text,
                        'title': sr.find('support-role-type').text,
                        'name': sr.find('contact-name').text
                    }
                )
            except AttributeError:
                pass

    return metadata_info

def make_datetime(date_string: str) -> datetime.datetime:
    if len(date_string)== 4:
        return datetime.datetime.strptime(date_string, '%Y')
    elif len(date_string) == 7:
        return datetime.datetime.strptime(date_string, '%Y-%m')
    else:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d')

def make_datetime_str(date_string) -> str:
    return make_datetime(date_string).isoformat() + "Z"


def process_one(
        feature: dict,
        src_crs: pyproj.CRS,
        dst_crs: pyproj.CRS,
        trn: pyproj.Transformer) -> Item:
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
    if 'support_roles' in metadata:
        for link in metadata['support_roles']:
            l = Link(rel=link['title'], target=link['href'], title=link['name'])
            item.add_link(l)
    item.add_asset('ept', asset)
    return item


def noaa_info(output_dir: str) -> ItemCollection:
    noaa_url = f'https://noaa-nos-coastal-lidar-pds.s3.us-east-1.amazonaws.com/laz/dav.json'

    resources = get_json_info(noaa_url)
    src_crs = pyproj.CRS.from_user_input(resources['crs']['properties']['name'])
    dst_crs = pyproj.CRS.from_epsg(4326)
    trn = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)

    item_list: List[Item] = [ ]
    catalog = Catalog(id = 'NOAA STAC', description='NOAA STAC Catalog of Lidar Items', catalog_type=CatalogType.SELF_CONTAINED)
    catalog.set_self_href(path.join(output_dir, 'catalog.json'))

    features = resources['features']
    full_count = len(features)

    for index, feature in enumerate(features):
        data_type = feature['properties']['DataType']
        name = feature['properties']['Name'].replace("/", "_")
        # Only currently handling lidar data type
        item = { }
        if data_type == 'Lidar':
            item = process_one(feature, src_crs, dst_crs, trn)
        else:
            continue

        if item:
            try:
                item.validate()
                item_list.append(item)

                output_path = path.join(output_dir, f'{name}.json')
                item_href = f'{name}.json'
                item.set_self_href(item_href)
                item_link = Link(rel=RelType.ITEM, target=item_href)
                catalog.add_link(item_link)

                # Write out Item
                with open(output_path, 'w') as output_file:
                    output_file.write(json.dumps(item.to_dict(), indent=2))
            except Exception as e:
                error_path = path.join(output_dir, 'errors')
                if not path.exists(error_path):
                    makedirs(error_path)
                error_file = path.join(error_path, name)
                with open(error_file, 'w') as error_out:
                    error_out.write(str(e))
        print(f'{index}/{full_count} done.')

    # Write out catalog
    catalog_path = path.join(output_dir, 'catalog.json')
    with open(catalog_path, 'w') as cat_file:
        cat_file.write(json.dumps(catalog.to_dict(), indent=2))

    # Write out item collection
    item_collection_path = path.join(output_dir, 'noaa_item_collection.json')
    ic = ItemCollection(item_list)
    with open(item_collection_path, 'w') as ic_file:
        ic_file.write(json.dumps(ic.to_dict(), indent=2))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--stac_directory", default="noaa_stac", type=str, help="Directory to put stac catalog")

    args = parser.parse_args()

    print(f"Writing out to {args.stac_directory}")

    if not path.exists(args.stac_directory):
        makedirs(args.stac_directory)

    noaa_info(args.stac_directory)

main()
