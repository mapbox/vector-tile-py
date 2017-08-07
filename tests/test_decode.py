from vector_tile import VectorTile, SplineFeature, PointFeature, PolygonFeature, LineStringFeature, Layer

test_data = open('tests/test.mvt', 'r').read()

def test_decode_vector_tile():
    vt = VectorTile(test_data)
    assert len(vt.layers) == 8
    
    # Test first layer
    layer = vt.layers[0]
    assert isinstance(layer, Layer)
    assert layer.name == 'points'
    assert layer.extent == 4096
    assert layer.dimensions == 2
    assert layer.version == 2
    assert len(layer.features) == 4
    # Test layer features
    expected_id = 2
    for feature in layer.features:
        assert isinstance(feature, PointFeature)
        assert feature.type == 'point'
        assert feature.id == expected_id
        geometry = feature.get_points()
        assert isinstance(geometry, list)
        assert len(geometry) == 1
        point = geometry[0]
        assert isinstance(point, list)
        assert len(point) == 2
        assert point[0] == 20
        assert point[1] == 20
        props = feature.properties
        assert isinstance(props, dict)
        assert len(props) == 1
        if expected_id == 2:
            assert props['some']
            assert props['some'] == 'attr'
        elif expected_id == 3:
            assert props['some']
            assert props['some'] == 'attr'
        elif expected_id == 4:
            assert props['some']
            assert props['some'] == 'otherattr'
        elif expected_id == 5:
            assert props['otherkey']
            assert props['otherkey'] == 'attr'
        expected_id += 1
