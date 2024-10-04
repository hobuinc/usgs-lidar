#usgs_boundary command

from .info import info


import logging
import sys

logger = logging.getLogger('usgs_boundary')

# create console handler and set level to debug
ch = logging.StreamHandler(stream=sys.stderr)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


def main():
    import argparse

    wesm_url = "https://apps.nationalmap.gov/lidar-explorer/lidar_ndx.json"

    parser = argparse.ArgumentParser(description="Compute boundaries for USGS 3DEP EPT PDS")
    parser.add_argument("bucket", type=str, help="Bucket to index")
    parser.add_argument("--stac_directory", default="stac_ept", type=str, help="Directory to put stac catalog")
    parser.add_argument("--stac_bucket", type=str, help="Bucket to output STAC info", default="usgs-lidar-stac")
    parser.add_argument("--layer", type=str, default="resources.geojson", help="Output GeoJSON file")
    parser.add_argument("--region", type=str, default="us-west-2", help="AWS region")
    parser.add_argument("--resolution", type=float, default=1000.0, help="Resolution for EPT selection")
    parser.add_argument("--limit", type=int, default=0, help="Limit processing to only this many")
    parser.add_argument("--wesm_url", type=str, default=wesm_url, help="WESM URL to reference for metadata.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    group.add_argument("-l", "--local_only", action="store_true")


    args = parser.parse_args()
    args.base_url = f'https://s3-{args.region}.amazonaws.com/{args.bucket}/'
    args.stac_base_url = f'https://s3-{args.region}.amazonaws.com/{args.stac_bucket}/ept/'

    info(args)


if __name__ == '__main__':
    main()
