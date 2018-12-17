vector-tile-py
==============

[![Build Status](https://travis-ci.org/mapbox/vector-tile-py.svg?branch=master)](https://travis-ci.org/mapbox/vector-tile-py)

DEPRECATED: the module is not being maintained and was never used for production purposes. For more actively developed vector tile libraries see https://github.com/mapbox/vector-tile-js (Javascript) and https://github.com/mapbox/vector-tile (C++)

This library reads [Mapbox Vector Tiles](https://github.com/mapbox/vector-tile-spec) and allows access to the layers and features.

It is only a very limited demo (only supports points) at this point and not a generic or multi-purpose library.

## Depends

 - Python 2.x || 3.x
 - Google protobuf python bindings

## Install

```
pip install -r requirements.txt --user
```

## Test

```
python tests.py
```

## Examples

Example showing how to create a vector tile with a single layer with a single feature with a point:

```
python example.py
```


Now let's get some real vector tile samples:

```
git clone https://github.com/mapbox/mvt-fixtures.git
```

We can inspect the tile data, printing a summary:

```
python tile-raw-info.py ./mvt-fixtures/real-world/nepal/13-6041-3426.mvt
````

We can also dump the data as GeoJSON:

```
python tile-info.py ./mvt-fixtures/real-world/nepal/13-6041-3426.mvt -t 13/6041/3426 > nepal.geojson
```


### Regenerating the protobuf bindings


```
git clone https://github.com/mapbox/vector-tile-spec.git
protoc ./vector-tile-spec/2.1/vector_tile.proto --python_out=vector_tile/ --proto_path ./vector-tile-spec/2.1/
```
