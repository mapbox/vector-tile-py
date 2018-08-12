#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json
from vector_tile import renderer
from vector_tile import vector_tile_pb2

from optparse import OptionParser


def stderr(*objs):
    print(*objs, file=sys.stderr)


if __name__ == "__main__" :
    usage = "usage: %prog "
    parser = OptionParser(usage=usage,
        description="Convert a Mapnik vector tile to GeoJSON")
    parser.add_option("-z", type="int", dest="z")
    parser.add_option("-x", type="int", dest="x")
    parser.add_option("-y", type="int", dest="y")
    parser.add_option("-t", type="string", dest="tile_address", default=None)
    parser.add_option("-l", "--layer", dest="layer", default=None)
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        stderr("No file name")
        sys.exit(0)

    if options.tile_address is not None:
        components = options.tile_address.split("/")
        zoom = int(components[0])
        x = int(components[1])
        y = int(components[2])
    elif options.z and options.x and options.y:
        zoom = options.z
        x = options.x
        y = options.y
    else:
        stderr("Error: no tile address, use -x -y and -z, or -t z/x/y")
        sys.exit(0)

    filename = args[0]
    if options.verbose:
        stderr("opening %s as tile %d/%d/%d" % (filename, zoom, x, y))
    with open(filename, "rb") as f:
        tile = vector_tile_pb2.Tile()
        decoded = f.read()

        tile.ParseFromString(decoded)
        req = renderer.Request(x,y,zoom)
        vtile = renderer.VectorTile(req, tile)
        vtile.layer = tile.Layer

        if options.layer:
            for layer in tile.layers:
                if layer.name == options.layer:
                    print(vtile.to_geojson(layer=layer, lonlat=True, layer_names=True))
                    break
        else:
            print(json.dumps(vtile.to_geojson(lonlat=True, layer_names=True), indent=4))

        if options.verbose:
            for layer in tile.layers:
                if options.verbose:
                    stderr("Layer: " + layer.name)
                    stderr("    Version: %d" % layer.version)
                    stderr("    Extent: %d" % layer.extent)
                    stderr("    %d Features" % len(layer.features))
                    stderr("    %d Keys" % len(layer.keys))
                    stderr("    %d Values" % len(layer.values))
