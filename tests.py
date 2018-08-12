#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest
import json

from vector_tile import renderer
from vector_tile import vector_tile_pb2

class TestRequestCtrans(unittest.TestCase):
    def test_lonlat2merc(self):
        # projection transform
        # should roughtly match: echo -180 -85 | cs2cs -f "%.10f" +init=epsg:4326 +to +init=epsg:3857
        x,y = renderer.lonlat2merc(-180,-85)
        self.assertAlmostEqual(-20037508.342789244,x)
        self.assertAlmostEqual(-19971868.8804085888,y)

    def test_box2d(self):
        box = renderer.Box2d(-180,-85,180,85)
        assert box.minx == -180
        assert box.miny == -85
        assert box.maxx == 180
        assert box.maxy == 85
        assert box.intersects(0,0)
        assert not box.intersects(-180,-90)
        self.assertAlmostEqual(box.bounds(),[box.minx,box.miny,box.maxx,box.maxy])

    def test_spherical_mercator(self):
        merc = renderer.SphericalMercator()
        z0_extent = merc.bbox(0,0,0)
        #todo this seems like it should test something

    def test_request_z0(self):
        zoom, x, y = 0, 0, 0
        req = renderer.Request(x,y,zoom)
        self.assertAlmostEqual(req.get_width(),40075016.68557849)
        self.assertAlmostEqual(req.get_height(),40075016.68557849)

    def test_request_z7(self):
        zoom, x, y = 7, 20, 49
        req = renderer.Request(x,y,zoom)
        assert req.zoom == zoom and req.x == x and req.y == y
        assert req.size == 256
        assert abs(req.get_width() - 313086.0700000003) < 1
        assert abs(req.get_height() - 313085.8099999996) < 1
        assert req.extent.intersects(-13469658, 4579425)# -121,38
        assert not req.extent.intersects(-14471533.80, 5621521.49)

    def test_ctrans_z0(self):
        req = renderer.Request(0,0,0)
        x,y = renderer.lonlat2merc(-180,-85)
        ctrans = renderer.CoordTransform(req)
        px,py = ctrans.forward(x,y)
        self.assertAlmostEqual(px,0.0)
        self.assertAlmostEqual(py,255.5806938147701)
        px2,py2 = ctrans.forward(-20037508.34,-20037508.34)
        self.assertAlmostEqual(px2,0.0)
        self.assertAlmostEqual(py2,256.0)
        px3,py3 = ctrans.forward(-20037508.34/2,-20037508.34/2)
        self.assertAlmostEqual(px2,0.0)
        self.assertAlmostEqual(py2,256.0)

    def test_ctrans_z7(self):
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

class TestTileCreation(unittest.TestCase):
    def test_layer_creation(self):
        """ Test creating an empty tile and an empty layer """
        req = renderer.Request(0,0,0)
        vtile = renderer.VectorTile(req)
        assert isinstance(vtile.tile, vector_tile_pb2.Tile)
        self.assertEqual(len(vtile.tile.layers), 0)
        layer = vtile.add_layer(name="points")
        assert layer is not None and isinstance(layer, vector_tile_pb2.Tile.Layer)
        self.assertEqual(len(vtile.tile.layers), 1)
        self.assertEqual(vtile.tile.layers[0], layer)
        self.assertEqual(len(layer.features), 0)

    def test_simple_tile_z0(self):
        """ Test creating a tile, adding a single layer and a single point """
        req = renderer.Request(0,0,0)
        vtile = renderer.VectorTile(req)
        #Test creating a layer
        layerName = "points"
        layer = vtile.add_layer(name=layerName)
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
        j_obj = vtile.to_geojson(layer_names=True, lonlat=True)
        assert isinstance(j_obj, dict)
        self.assertEqual(j_obj["type"], "FeatureCollection")
        self.assertEqual(len(j_obj["features"]), 1)
        self.assertEqual(j_obj["features"][0]["geometry"]["type"], "Point")
        self.assertEqual(len(j_obj["features"][0]["geometry"]["coordinates"]), 2)
        self.assertAlmostEqual(j_obj["features"][0]["geometry"]["coordinates"][0], lng, 0)
        self.assertAlmostEqual(j_obj["features"][0]["geometry"]["coordinates"][1], lat, 0)
        self.assertEqual(j_obj["features"][0]["properties"]["layer"], layerName)
        self.assertEqual(j_obj["features"][0]["properties"]["hello"], "world")
        #now dump tile to protocol buffer message
        pbf = vtile.to_message()
        assert len(pbf) > 0
        tile = vector_tile_pb2.Tile()
        tile.ParseFromString(pbf)
        vtile2 = renderer.VectorTile(req, tile)
        j_obj_deserialized = vtile2.to_geojson(layer_names=True, lonlat=True)
        self.assertDictEqual(j_obj, j_obj_deserialized)

    def test_attribute_types(self):
        """ Test that all attribute types are handled correctly """
        req = renderer.Request(0,0,0)
        vtile = renderer.VectorTile(req)
        layer = vtile.add_layer(name="points")
        attr = {"name":"DC",
                "integer":10,
                "bigint":sys.maxsize,
                "nbigint":-1 * sys.maxsize,
                "float":1.5,
                "bigfloat":float(sys.maxsize),
                "unistr":u"élan",
                "bool":True,
                "bool2":False
                }
        vtile.add_point(layer,0,0,attr)
        j_obj = vtile.to_geojson()
        self.assertEqual(j_obj['type'],"FeatureCollection")
        self.assertEqual(len(j_obj['features']),1)
        feature = j_obj['features'][0]
        self.assertDictEqual(feature['properties'],attr)

    def test_key_value_deduplication(self):
        """ Test that keys and values are properly deduplicated """
        req = renderer.Request(0,0,0)
        vtile = renderer.VectorTile(req)
        layer = vtile.add_layer(name="points")
        assert len(layer.keys) == 0 and len(layer.values) == 0
        width = req.get_width()
        height = req.get_height()
        attr = {"hello":"world"}
        #add a point, it should add 1 key and 1 value
        vtile.add_point(layer, width*.1, height*.1, attr)
        assert len(layer.keys) == 1 and len(layer.values) == 1
        #add another feature with the same key and value
        vtile.add_point(layer, width*.2, height*.2, attr)
        assert len(layer.keys) == 1 and len(layer.values) == 1
        #add another feature with existing key and new value
        vtile.add_point(layer, width*.4, height*.3, {"hello":"mars"})
        assert len(layer.keys) == 1 and len(layer.values) == 2
        #add another feature with an existing value and a new key
        vtile.add_point(layer, width*.5, height*.5, {"goodbye":"world"})
        assert len(layer.keys) == 2 and len(layer.values) == 2

    def test_adding_duplicate_points(self):
        """ Test that points are deduplicated """
        req = renderer.Request(0,0,0)
        vtile = renderer.VectorTile(req)
        layer = vtile.add_layer(name="points")
        vtile.add_point(layer, 0,0,{})
        vtile.add_point(layer, 0,0,{})
        self.assertEqual(len(layer.features), 1)
        j_obj = vtile.to_geojson()
        self.assertEqual(len(j_obj['features']),1)

    def test_vtile_z0(self):
        """ Test adding points at zoom 0 """
        req = renderer.Request(0,0,0)
        vtile = renderer.VectorTile(req)
        layer = vtile.add_layer(name="points")
        x,y = -8526703.378081053, 4740318.745473632
        vtile.add_point(layer,x,y,{})
        j_obj = vtile.to_geojson()
        feature = j_obj['features'][0]
        coords = feature['geometry']['coordinates']
        self.assertAlmostEqual(coords[0],x,-4)
        self.assertAlmostEqual(coords[1],y,-4)

    def test_vtile_z20(self):
        """ Test adding points at zoom 20 """
        merc = renderer.SphericalMercator()
        x,y = -8526703.378081053, 4740318.745473632
        xyz_bounds = merc.xyz([x,y,x,y],20)
        req = renderer.Request(xyz_bounds[0],xyz_bounds[1],20)
        vtile = renderer.VectorTile(req)
        layer = vtile.add_layer(name="points")
        vtile.add_point(layer,x,y,{})
        j_obj = vtile.to_geojson()
        feature = j_obj['features'][0]
        coords = feature['geometry']['coordinates']
        self.assertAlmostEqual(coords[0],x,2)
        self.assertAlmostEqual(coords[1],y,2)

    def test_vtile_z20_higher_precision(self):
        """ Test adding points at zoom 20 with larger than standard path multiplier """
        merc = renderer.SphericalMercator()
        x,y = -8526703.378081053, 4740318.745473632
        xyz_bounds = merc.xyz([x,y,x,y],20)
        req = renderer.Request(xyz_bounds[0],xyz_bounds[1],20)
        vtile = renderer.VectorTile(req,path_multiplier=512)
        layer = vtile.add_layer(name="points")
        vtile.add_point(layer,x,y,{})
        j_obj = vtile.to_geojson()
        feature = j_obj['features'][0]
        coords = feature['geometry']['coordinates']
        self.assertAlmostEqual(coords[0],x,3)
        self.assertAlmostEqual(coords[1],y,3)

    def test_vtile_z22(self):
        """ Test adding points at zoom 22 """
        merc = renderer.SphericalMercator()
        x,y = -8526703.378081053, 4740318.745473632
        xyz_bounds = merc.xyz([x,y,x,y],22)
        req = renderer.Request(xyz_bounds[0],xyz_bounds[1],22)
        vtile = renderer.VectorTile(req)
        layer = vtile.add_layer(name="points")
        vtile.add_point(layer,x,y,{})
        j_obj = vtile.to_geojson()
        feature = j_obj['features'][0]
        coords = feature['geometry']['coordinates']
        self.assertAlmostEqual(coords[0],x,2)
        self.assertAlmostEqual(coords[1],y,1)

    def test_vtile_z22_higher_precision(self):
        """ Test adding points at zoom 22 with larger than standard path multiplier """
        merc = renderer.SphericalMercator()
        x,y = -8526703.378081053, 4740318.745473632
        xyz_bounds = merc.xyz([x,y,x,y],22)
        req = renderer.Request(xyz_bounds[0],xyz_bounds[1],22)
        vtile = renderer.VectorTile(req,path_multiplier=512)
        layer = vtile.add_layer(name="points")
        vtile.add_point(layer,x,y,{})
        j_obj = vtile.to_geojson()
        feature = j_obj['features'][0]
        coords = feature['geometry']['coordinates']
        self.assertAlmostEqual(coords[0],x,4)
        self.assertAlmostEqual(coords[1],y,4)


if __name__ == '__main__':
    unittest.main()
