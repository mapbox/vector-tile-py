from vector_tile import VectorTile

def test_no_layers():
    vt = VectorTile()
    assert len(vt.serialize()) == 0
