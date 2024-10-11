import pystac
from .metadata import MetaCatalog

WESM_URL = 'https://apps.nationalmap.gov/lidar-explorer/lidar_ndx.json'

def usgs_stac():
    # coordinate usage of wesm metadata objects
    # m = Meta
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, help="Url for WESM JSON",
            default=WESM_URL)
    parser.add_argument("--dst", type=str, help="Destination directory",
            default='./wesm_stac/')
    parser.add_argument("--stac_bucket", type=str, help="Bucket for root STAC href.", default="usgs-lidar-stac")

    args = parser.parse_args()
    m = MetaCatalog(args.url, args.dst, )
    m.set_children()
    c = m.get_stac()
    c.normalize_hrefs(args.dst)


if __name__ == '__main__':
    usgs_stac()