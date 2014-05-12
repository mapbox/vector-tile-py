#!/usr/bin/env python

import json
import logging
import sys

import vector_tile

def open_output(arg):
    """Returns an opened output stream."""
    if arg == sys.stdout:
        return arg
    else:
        return open(arg, 'w')

def main(infile, outfile):
    with open_output(outfile) as sink, open(infile) as source:
        collection = json.load(source)
        layer = vector_tile.layer(source.name, collection['features'])
        tile = vector_tile.tile([layer])
        sink.write(tile.SerializeToString())
    return 0

if __name__ == '__main__':

    import argparse

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logger = logging.getLogger('vector_tile.tool')

    parser = argparse.ArgumentParser(
        description="Serialize a GeoJSON collection to Protobuf Vector Tile")
    parser.add_argument('infile', 
        help="input file name")
    parser.add_argument('outfile',
        nargs='?', 
        help="output file name, defaults to stdout if omitted", 
        default=sys.stdout)
    args = parser.parse_args()

    sys.exit(main(args.infile, args.outfile))

