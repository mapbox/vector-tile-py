
from collections import defaultdict
from itertools import chain, tee
import sys
try:
    # Python 2
    from future_builtins import filter, map, zip
except ImportError:
    # Python 3
    pass

from vector_tile import vector_tile_pb2


__version__ = "0.1"


geom_type_map = {
    'Unknown': 0,
    'Point': 1,
    'LineString': 2,
    'Polygon': 3 }

if sys.version_info.major == 3:
    value_type_map = {
        str: 'string_value',
        float: 'double_value',
        int: 'int_value',
        bool: 'bool_value' }
else:
    value_type_map = {
        unicode: 'string_value',
        str: 'string_value',
        float: 'double_value',
        int: 'int_value',
        bool: 'bool_value' }

def value(ob):
    v = vector_tile_pb2.Tile.value()
    setattr(v, value_type_map[type(ob)], ob)
    return v

def singles(f):
    g = f.get('geometry')
    if not g:
        yield f
    if g:
        gtype = g['type']
        coords = g['coordinates']
        if gtype.startswith('Multi'):
            for i, part in enumerate(coords):
                ob = f.copy()
                ob['geometry'] = {'type': gtype[5:], 'coordinates': part}
                ob['id'] = str(ob.get('id', id(ob))) + "-%d" % i
                yield ob
        else:
            yield f

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def layer(name, features):
    """Make a vector_tile.Tile.Layer from GeoJSON features."""
    pbl = vector_tile_pb2.tile.layer()
    pbl.name = name
    pbl.version = 1

    pb_keys = []
    pb_vals = []
    pb_features = []

    for j, f in enumerate(
            chain.from_iterable(singles(ob) for ob in features)):
        pbf = vector_tile_pb2.tile.feature()
        pbf.id = j

        # Pack up the feature geometry.
        g = f.get('geometry')
        if g:
            gtype = g['type']
            coords = g['coordinates']
            if gtype == 'Point':
                geometry = [(1<<3)+1] + [
                    (n << 1) ^ (n >> 31) for n in map(int, coords)]
            elif gtype == 'LineString':
                num = len(coords)
                geometry = [0]*(4 + 2*(num-1))
                geometry[0] = (1<<3)+1
                geometry[1:3] = (
                    (n << 1) ^ (n >> 31) for n in map(int, coords[0]))
                geometry[3] = ((num-1)<<3)+2
                for i, (prev, pair) in enumerate(pairwise(coords), 1):
                    prev = map(int, prev)
                    pair = map(int, pair)
                    geometry[2*i+2:2*i+4] = (
                        (n << 1) ^ (n >> 31) for n in (
                            pair[0]-prev[0], pair[1]-prev[1]))
                pbf.geometry.extend(geometry)
            elif gtype == 'Polygon':
                rings = []
                for ring in coords:
                    num = len(ring)
                    geometry = [0]*(5 + 2*(num-1))
                    geometry[0] = (1<<3)+1
                    geometry[1:3] = (
                        (n << 1) ^ (n >> 31) for n in map(int, ring[0]))
                    geometry[3] = ((num-1)<<3)+2
                    for i, (prev, pair) in enumerate(pairwise(ring), 1):
                        prev = map(int, prev)
                        pair = map(int, pair)
                        geometry[2*i+2:2*i+4] = (
                            (n << 1) ^ (n >> 31) for n in (
                                pair[0]-prev[0], pair[1]-prev[1]))
                    geometry[-1] = (1<<3)+7
                    pbf.geometry.extend(geometry)

            pbf.type = geom_type_map[gtype]

        # Pack up feature properties.
        props = f.get('properties', {})
        tags = [0]*(2*len(props))
        for i, (k, v) in enumerate(props.items()):
            if k not in pb_keys:
                pb_keys.append(k)
            if v not in pb_vals:
                pb_vals.append(v)
            tags[i*2:i*2+2] = pb_keys.index(k), pb_vals.index(v)
        pbf.tags.extend(tags)
        pb_features.append(pbf)

    # Finish up the layer.
    pbl.keys.extend(map(str, pb_keys))
    pbl.values.extend(map(value, filter(None, pb_vals)))

    return pbl

def tile(layers):
    pbt = vector_tile_pb2.tile()
    pbt.layers.extend(list(layers))
    return pbt

def mapping(feature):
    """Make a GeoJSON mapping from a vector_tile.Tile.Feature."""
    return {
        'type': 'Feature',
        'id': feature.id,
        'properties': {},
        'geometry': None }
