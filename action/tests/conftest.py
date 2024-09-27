import pytest
import dask
from typing import Generator, Any

from usgs_boundary.metadata import MetaCatalog

@pytest.fixture(autouse=True)
def dask_conf():
    dask.config.set({'scheduler':'single-threaded'})
    yield

@pytest.fixture
def wesm_url():
    yield 'https://apps.nationalmap.gov/lidar-explorer/lidar_ndx.json'

@pytest.fixture
def catalog(wesm_url: str):
    yield MetaCatalog(wesm_url)

@pytest.fixture
def meta_json():
    yield {
        "FESMProjectID": "WA_PSLC_2000",
        "Entwined": "False",
        "EntwinePath": "",
        "LAZinCloud": "True",
        "FolderName": "legacy/WA_PSLC_2000",
        "workunit": "WA_PSLC_2000",
        "workunit_id": -1694,
        "project": "WA_PSLC_2000_Legacy_Data",
        "project_id": -16940,
        "collect_start": "2000/12/01",
        "collect_end": "2001/01/30",
        "ql": "Other",
        "spec": "Other",
        "p_method": "linear-mode lidar",
        "dem_gsd_meters": 3.0,
        "horiz_crs": "2285",
        "vert_crs": "6360",
        "geoid": "GEOID99",
        "lpc_pub_date": "2013/04/22",
        "lpc_update": None,
        "lpc_category": "Does not meet",
        "lpc_reason": "LPC predates v.1.0 or draft LBS",
        "sourcedem_pub_date": None,
        "sourcedem_update": None,
        "sourcedem_category": "Does not meet",
        "sourcedem_reason": "LPC does not meet",
        "onemeter_category": "Does not meet",
        "onemeter_reason": "LPC does not meet",
        "seamless_category": "Does not meet",
        "seamless_reason": "LPC does not meet",
        "lpc_link": "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/legacy/WA_PSLC_2000",
        "sourcedem_link": None,
        "metadata_link": "http://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/metadata/legacy/WA_PSLC_2000",
        "bbox": "-123.1255, 47.3224, -121.7862, 47.9516"
    }