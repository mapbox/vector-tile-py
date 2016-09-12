import os
from pbf_reader import PBFReader

filename = './Feature-single-linestring.mvt'

data = bytearray(os.path.getsize(filename))
with open(filename, "rb") as f:
    f.readinto(data);
    buffered_data = buffer(data)
    tile_reader = PBFReader(buffered_data)
    while tile_reader.next():
        # get layer message in tile message
        if tile_reader.get_tag() == 3:
            layers_data = tile_reader.view()
            layer_reader = PBFReader(layers_data);
            while layer_reader.next():
                # get feature message in layer message
                if layer_reader.get_tag() == 2: 
                    features_data = layer_reader.view()
                    feature_reader = PBFReader(features_data)
                    while feature_reader.next():
                        # get geometry array in feature message
                        if feature_reader.get_tag() == 4:
                            print feature_reader.get_packed_uint32()
                        else:
                            feature_reader.skip()
                else:
                    layer_reader.skip()
        else:
            tile_reader.skip()
