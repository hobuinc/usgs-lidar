from typing import Any
from pathlib import Path

from usgs_boundary.metadata import MetaCatalog, MetaCollection, MetaItem

def test_meta_url(wesm_url: str) -> None:
    m = MetaCatalog(wesm_url)
    assert m.url == wesm_url
    assert m.meta_bag == None
    l = m.create_collections().compute()
    assert len(l) == 2920

def test_metadata(meta_json: dict[str, Any]) -> None:
    m = MetaCollection(meta_json)

    assert m.id == meta_json['FESMProjectID']
    assert m.hcrs == meta_json['horiz_crs']
    assert m.vcrs == meta_json['vert_crs']
    assert m.pc_path == Path(meta_json['lpc_link'] , 'LAZ/')
    assert m.meta_link == meta_json['metadata_link']
    assert m.collect_start == meta_json['collect_start']
    assert m.collect_end == meta_json['collect_end']

def test_item(meta_json: dict[str, Any]):
    # TODO get this test running. Make sure that STAC Items are being created
    # correctly from the Meta objects
    m = MetaCollection(meta_json)
    m.set_pc_paths()
    pc_path = m.pc_paths[0]
    meta_path = m.sidecar_paths[0]

    mi = MetaItem(pc_path, meta_path, m)
    item = mi.get_stac()
