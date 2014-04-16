#!/usr/bin/env python
# -*- coding: utf-8 -*-

from vector_tile import renderer
from vector_tile import vector_tile_pb2

def test_latlon2merc():
    """ test trnasformation between epsg:4326 and epsg:3857"""
    lat, lng = 38, -121
    x,y = renderer.lonlat2merc(lng,lat)
    assert abs(x - -13469658) < 1
    assert abs(y - 4579425) < 1
    x,y = renderer.merc2lonlat(x,y)
    assert abs(x - lng) < 0.000001
    assert abs(y - lat) < 0.000001

def test_request():
    """ Test render.Request """
    zoom, x, y = 7, 20, 49
    req = renderer.Request(x,y,zoom)

    assert req.zoom == zoom and req.x == x and req.y == y
    assert req.size == 256
    assert abs(req.get_width() - 313086.0700000003) < 1
    assert abs(req.get_height() - 313085.8099999996) < 1
    assert req.extent.intersects(-13469658, 4579425)# -121,38
    assert not req.extent.intersects(-14471533.80, 5621521.49)

def test_coord_transform():
    """ Test render.CoordTransform """
    zoom, x, y = 7, 20, 49
    req = renderer.Request(x,y,zoom)
    transform = renderer.CoordTransform(req)

    testX, testY = -13469658, 4579425
    projectedX, projectedY = transform.forward(testX, testY)
    assert projectedX > 0 and projectedX < 256
    assert projectedY > 0 and projectedY < 256
    reversedX, reversedY = transform.backward(projectedX, projectedY)
    assert abs(testX - reversedX) < 1
    assert abs(testY - reversedY) < 1

def test_simple_tile():
    """ Test creating a tile, adding a single layer and a single point """
    zoom, x, y = 7, 20, 49
    req = renderer.Request(x,y,zoom)
    vtile = renderer.VectorTile(req)
    assert isinstance(vtile.tile, vector_tile_pb2.tile)
    assert len(vtile.tile.layers) == 0
    #Test creating a layer
    layerName = "points"
    layer = vtile.add_layer(name=layerName)
    assert layer is not None and isinstance(layer, vector_tile_pb2.tile.layer)
    assert len(vtile.tile.layers) == 1 and vtile.tile.layers[0] == layer
    assert len(layer.features) == 0
    #test adding a point feature
    lat, lng = 38, -121
    attr = {"hello":"world"}
    x,y = renderer.lonlat2merc(lng,lat)
    assert vtile.add_point(layer,x,y,attr)
    assert len(layer.features) == 1
    feature = layer.features[0]
    key_id = feature.tags[0]
    value_id = feature.tags[1]
    key = str(layer.keys[key_id])
    assert key == "hello"
    value = layer.values[value_id]
    assert value.HasField('string_value')
    assert value.string_value == "world"
    #dump the layer to GeoJSON and make sure the output matches the input
    layerJson = vtile.to_geojson(layer=layer, lonlat=True, layer_names=True)
    assert isinstance(layerJson, dict)
    assert layerJson["type"] == "FeatureCollection"
    assert len(layerJson["features"]) == 1
    assert layerJson["features"][0]["geometry"]["type"] == "Point"
    assert len(layerJson["features"][0]["geometry"]["coordinates"]) == 2
    assert abs(layerJson["features"][0]["geometry"]["coordinates"][0] - lng) < 0.001
    assert abs(layerJson["features"][0]["geometry"]["coordinates"][1] - lat) < 0.001
    assert layerJson["features"][0]["properties"]["layer"] == layerName
    assert layerJson["features"][0]["properties"]["hello"] == "world"

def test_key_value_deduplication():
    """ Test that keys and values are properly dedeuplicated """
    zoom, x, y = 7, 20, 49
    req = renderer.Request(x,y,zoom)
    vtile = renderer.VectorTile(req)
    layer = vtile.add_layer(name="points")
    assert len(layer.keys) == 0 and len(layer.values) == 0

    lat, lng = 38, -121
    attr = {"hello":"world"}
    x,y = renderer.lonlat2merc(lng,lat)
    vtile.add_point(layer, x, y, attr)
    assert len(layer.keys) == 1 and len(layer.values) == 1
    #add another feature with the same key and value
    vtile.add_point(layer, x+1, y+1, attr)
    assert len(layer.keys) == 1 and len(layer.values) == 1
    #add another feature with same key, but different value
    vtile.add_point(layer, x+2, y+2, {"hello":"mars"})
    assert len(layer.keys) == 1 and len(layer.values) == 2
    vtile.add_point(layer, x+3, y+3, {"goodbye":"world"})
    assert len(layer.keys) == 2 and len(layer.values) == 2
