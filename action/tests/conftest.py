import pytest
import dask

from usgs_boundary.metadata import MetaCatalog, logger

@pytest.fixture(autouse=True)
def dask_conf():
    dask.config.set({'scheduler':'threading'})
    yield

@pytest.fixture(autouse=True)
def log():
    logger.setLevel('DEBUG')

@pytest.fixture
def wesm_url():
    yield 'https://apps.nationalmap.gov/lidar-explorer/lidar_ndx.json'

@pytest.fixture
def catalog(wesm_url: str):
    yield MetaCatalog(wesm_url)

@pytest.fixture
def meta_json():
    yield {
        "FESMProjectID": "WY_YELLOWSTONENP_1RF_2020",
        "Entwined": "True",
        "EntwinePath": "WY_YellowstoneNP_1RF_2020",
        "LAZinCloud": "True",
        "FolderName": "WY_YellowstoneNP_2020_D20/WY_YellowstoneNP_1RF_2020",
        "workunit": "WY_YellowstoneNP_1RF_2020",
        "workunit_id": 225074,
        "project": "WY_YellowstoneNP_2020_D20",
        "project_id": 196958,
        "collect_start": "2020/09/21",
        "collect_end": "2021/09/13",
        "ql": "QL 2",
        "spec": "USGS Lidar Base Specification 2.1",
        "p_method": "linear-mode lidar",
        "dem_gsd_meters": 1.0,
        "horiz_crs": "6341",
        "vert_crs": "5703",
        "geoid": "GEOID18",
        "lpc_pub_date": "2022/12/14",
        "lpc_update": None,
        "lpc_category": "Meets",
        "lpc_reason": "Meets 3DEP LPC requirements",
        "sourcedem_pub_date": "2022/12/14",
        "sourcedem_update": None,
        "sourcedem_category": "Meets",
        "sourcedem_reason": "Meets 3DEP source DEM requirements",
        "onemeter_category": "Meets",
        "onemeter_reason": "Meets 3DEP 1-m DEM requirements",
        "seamless_category": "Meets",
        "seamless_reason": "Meets 3DEP seamless DEM requirements",
        "lpc_link": "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/WY_YellowstoneNP_2020_D20/WY_YellowstoneNP_1RF_2020",
        "sourcedem_link": "http://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/OPR/Projects/WY_YellowstoneNP_2020_D20/WY_YellowstoneNP_1RF_2020",
        "metadata_link": "http://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/metadata/WY_YellowstoneNP_2020_D20/WY_YellowstoneNP_1RF_2020",
        "bbox": "-110.4908935097, 45.1792846597, -110.4780893877, 45.1883487461"
    }