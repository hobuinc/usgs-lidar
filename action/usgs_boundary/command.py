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

    parser = argparse.ArgumentParser(description="Compute boundaries for USGS 3DEP EPT PDS")
    parser.add_argument("bucket", type=str, help="Bucket to index")
    parser.add_argument("--layer", type=str, default="resources.geojson", help="Output GeoJSON file")
    parser.add_argument("--resolution", type=float, default=1000.0, help="Resolution for EPT selection")
    parser.add_argument("--limit", type=int, default=0, help="Limit processing to only this many")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")


    args = parser.parse_args()


    info(args)





