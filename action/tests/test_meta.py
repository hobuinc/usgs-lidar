from typing import Any
from pathlib import Path

from usgs_boundary.metadata import MetaCatalog, MetaCollection, MetaItem, WesmMetadata
from usgs_boundary.metadata import get_date

def test_meta_url(wesm_url: str) -> None:
    m = MetaCatalog(wesm_url)
    assert m.url == wesm_url
    assert m.children == None
    # reset and make a more reasonable size for testing
    obj = m.obj
    m.obj = {}
    for i, kv in enumerate(obj.items()):
        if i >= 5:
            break
        m.obj[kv[0]] = kv[1]

    l = m.set_children()
    assert m.catalog.validate()
    assert len(m.children) == 5

def test_metadata(meta_json: dict[str, Any]) -> None:
    m = WesmMetadata(**meta_json)

    assert m.FESMProjectID == meta_json['FESMProjectID']
    assert m.horiz_crs == meta_json['horiz_crs']
    assert m.vert_crs == meta_json['vert_crs']
    assert m.metadata_link == meta_json['metadata_link']
    assert m.collect_start == get_date(meta_json['collect_start'])
    assert m.collect_end == get_date(meta_json['collect_end'])

def test_item(meta_json: dict[str, Any]):
    # TODO get this test running. Make sure that STAC Items are being created
    # correctly from the Meta objects
    m = MetaCollection(meta_json)
    assert m.collection.validate()

    m.set_paths()
    pc_path = m.pc_paths[0]
    meta_path = m.sidecar_paths[0]

    mi = MetaItem(pc_path, meta_path, m.meta)
    item = mi.get_stac()
    assert item.validate()


def test_full_loop(wesm_url: dict[str, Any], dst_dir):
    m = MetaCatalog(wesm_url, dst_dir)
    assert m.url == wesm_url
    assert m.children == []
    # reset and make a more reasonable size for testing
    obj = {
        "WA_PSLC_2000": m.obj["WA_PSLC_2000"],
        "WY_YELLOWSTONENP_1RF_2020": m.obj["WY_YELLOWSTONENP_1RF_2020"]
    }
    m.obj = {}
    for i, kv in enumerate(obj.items()):
        if i >= 3:
            break
        m.obj[kv[0]] = kv[1]

    l = m.set_children(recursive=True)
    m.catalog.normalize_hrefs('./usgs_stac/')
    assert m.catalog.validate()