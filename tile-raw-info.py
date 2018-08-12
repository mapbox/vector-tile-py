#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import codecs
from vector_tile import vector_tile_pb2
from optparse import OptionParser


def get_array_values(a_list):
    output_str = u""
    for v in a_list:
        output_str += u"{},".format(v)
    return output_str[:-1]


def get_pbf_value(val):
    if val.HasField('string_value'):
        v = val.string_value
    elif val.HasField('int_value'):
        v = val.int_value
    elif val.HasField('double_value'):
        v = val.double_value
    elif val.HasField('float_value'):
        v = val.float_value
    elif val.HasField('bool_value'):
        v = val.bool_value
    else:
        v = u"null"
    return v


def stderr(*objs):
    print(*objs, file=sys.stderr)


if __name__ == "__main__":
    usage = "usage: %prog "
    parser = OptionParser(usage=usage,
        description="Output information in a Mapnik vector tile.")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", default=False)
    (options, args) = parser.parse_args()

    if len(args) != 1:
        stderr("No file name")
        sys.exit(0)

    filename = args[0]
    with open(filename, "rb") as f:
        tile = vector_tile_pb2.Tile()
        decoded = f.read()

        tile.ParseFromString(decoded)

        SEG_END    = 0
        SEG_MOVETO = 1
        SEG_LINETO = 2
        SEG_CLOSE = (0x40 | 0x0f)

        if options.verbose:
            # print out each layer and feature's raw data.
            output_str = u""
            for layer in tile.layers:
                stderr("layer: {}".format(layer.name))
                stderr("  version: {}".format(layer.version))
                stderr("  extent: {}".format(layer.extent))
                key_vals = get_array_values(layer.keys)
                stderr(u"  keys: {}".format(key_vals))
                output_str = u""
                for val in layer.values:
                    v = get_pbf_value(val)
                    output_str += u"{},".format(v)
                output_str = output_str[:-1]
                stderr(u"  values: {}".format(output_str))
                output_str = u""
                for f in layer.features:
                    stderr("  feature: {}".format(f.id))
                    feat_type = f.type
                    if feat_type == 0:
                        output_str = "Unknown"
                    elif feat_type == 1:
                        output_str = "Point"
                    elif feat_type == 2:
                        output_str = "LineString"
                    elif feat_type == 3:
                        output_str = "Polygon"
                    stderr("    type: {}".format(output_str))
                    output_str = u""
                    tag_vals = get_array_values(f.tags)
                    stderr(u"    tags: {}".format(tag_vals))
                    geo_vals = get_array_values(f.geometry)
                    stderr(u"    geometries: {}".format(geo_vals))
                stderr("")
        else:
            # just print out the aggregate info for each layer.
            stderr("layers: {}".format(len(tile.layers)))
            for layer in tile.layers:
                stderr("{}:".format(layer.name))
                stderr("  version: {}".format(layer.version))
                stderr("  extent: {}".format(layer.extent))
                stderr("  features: {}".format(len(layer.features)))
                stderr("  keys: {}".format(len(layer.keys)))
                stderr("  values: {}".format(len(layer.values)))
                total_repeated = 0
                num_commands = 0
                num_move_to = 0
                num_line_to = 0
                num_close = 0
                num_empty = 0
                degenerate = 0
                for feat in layer.features:
                    total_repeated += len(feat.geometry)
                    g_type = feat.type
                    cmd = -1
                    cmd_bits = 3
                    length = 0
                    g_length = 0
                    k = 0
                    while k < len(feat.geometry):
                        if length == 0:
                            cmd_len = feat.geometry[k]
                            #stderr("geom: {}".format(cmd_len))
                            k += 1
                            cmd = cmd_len & ((1 << cmd_bits) - 1)
                            length = cmd_len >> cmd_bits
                            if length <= 0:
                                num_empty += 1
                            num_commands += 1
                            g_length = 0
                        if length > 0:
                            length -= 1
                            if cmd == SEG_MOVETO or cmd == SEG_LINETO:
                                #stderr("geom: {}".format(feat.geometry[k]))
                                #stderr("geom: {}".format(feat.geometry[k+1]))
                                k += 2
                                g_length += 1
                                if cmd == SEG_MOVETO:
                                    num_move_to += 1
                                    #stderr("move to!")
                                elif cmd == SEG_LINETO:
                                    num_line_to += 1
                                    #stderr("line to!")
                            elif cmd == (SEG_CLOSE & ((1 << cmd_bits) - 1)):
                                #stderr("close!")
                                if g_length <= 2:
                                    degenerate += 1
                                num_close += 1
                            else:
                                err = 'unknown command type: {}'.format(cmd)
                                raise ValueError(err)

                stderr("  geometry summary:")
                stderr("    total: {}".format(total_repeated))
                stderr("    commands: {}".format(num_commands))
                stderr("    move_to: {}".format(num_move_to))
                stderr("    line_to: {}".format(num_line_to))
                stderr("    close: {}".format(num_close))
                stderr("    degenerate polygons: {}".format(degenerate))
                stderr("    empty geoms: {}".format(num_empty))
