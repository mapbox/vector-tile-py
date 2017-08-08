import pytest
from vector_tile import VectorTile, SplineFeature, PointFeature, PolygonFeature, LineStringFeature, Layer, FeatureProperties

def test_no_layers():
    vt = VectorTile()
    assert len(vt.serialize()) == 0

def test_create_layer():
    vt = VectorTile()
    layer = vt.add_layer('point')
    assert layer.name == 'point'
    assert layer.dimensions == 2
    assert layer.version == 2
    assert isinstance(layer, Layer)
    layer = vt.add_layer('point_3d', 3)
    assert layer.name == 'point_3d'
    assert layer.dimensions == 3
    assert layer.version == 2
    assert isinstance(layer, Layer)
    layer = vt.add_layer('point_4d', 4, 4)
    assert layer.name == 'point_4d'
    assert layer.dimensions == 4
    assert layer.version == 4
    assert isinstance(layer, Layer)

def test_layer_extent():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert layer.extent == 4096
    layer.extent = 8000
    assert layer.extent == 8000

def test_layer_name():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert layer.name == 'test'
    layer.name = 'foo'
    assert layer.name == 'foo'

def test_layer_dimensions():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert layer.dimensions == 2
    with pytest.raises(AttributeError):
        layer.dimensions = 3
    assert layer.dimensions == 2

def test_layer_features():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert len(layer.features) == 0
    assert isinstance(layer.features, list)
    with pytest.raises(AttributeError):
        layer.features = [1,2]
    assert len(layer.features) == 0

def test_feature_properties():
    vt = VectorTile()
    layer = vt.add_layer('test')
    feature = layer.add_point_feature()
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    prop = feature.properties
    assert isinstance(prop, FeatureProperties)
    assert feature.properties == {}
    assert prop == {}
    prop['fun'] = 'stuff'
    assert 'fun' in prop
    assert prop['fun'] == 'stuff'
    assert feature.properties['fun'] == 'stuff'
    assert feature.properties == {'fun':'stuff'}
    # Can set by external dictionary
    prop_dict = { 'number': 1, 'bool': True, 'string': 'foo', 'float': 4.1 }
    feature.properties = prop_dict
    assert feature.properties == prop_dict
    # Key error on not existant property
    with pytest.raises(KeyError):
        foo = feature.properties['doesnotexist']
    # Type errors on invalid key types
    with pytest.raises(TypeError):
        feature.properties[1.234] = True
    with pytest.raises(TypeError):
        feature.properties[1] = True
    with pytest.raises(TypeError):
        foo = feature.properties[1.234]
    with pytest.raises(TypeError):
        foo = feature.properties[1]
    # During setting invalid properties with bad keys or value types will just be dropped
    prop_dict = {'foo': [1,2,3], 'fee': {'a':'b'}, 1.2341: 'stuff', 1: 'fish', 'go': False }
    feature.properties = prop_dict
    assert feature.properties != prop_dict
    assert feature.properties == { 'go': False }

def test_create_point_feature():
    vt = VectorTile()
    layer = vt.add_layer('test')
    feature = layer.add_point_feature()
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]


def test_create_line_feature():
    vt = VectorTile()
    layer = vt.add_layer('test')
    feature = layer.add_line_string_feature()
    assert isinstance(feature, LineStringFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
