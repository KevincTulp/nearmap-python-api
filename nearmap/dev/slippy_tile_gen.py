from pathlib import Path
from osgeo.gdal import Translate
from math import log, tan, radians, cos, atan, sinh, pi, degrees
import fiona
from fiona.transform import transform_geom
from shapely.geometry import Polygon, box, shape
from shapely import ops
import tiletanic
import geopandas as gpd
from collections import defaultdict

import time
try:
    from ujson import load, dump, dumps
except ModuleNotFoundError:
    from json import load, dump, dumps


def sec(x):
    return 1 / cos(x)


def latlon_to_xy(lat, lon, z):
    tile_count = pow(2, z)
    xtile = (lon + 180) / 360
    ytile = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return int(tile_count * xtile), int(tile_count * ytile)


def xy_to_latlon(xtile, ytile, z):
    n = pow(2, z)
    lon_deg = (xtile / n * 360.0) - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return lat_deg, lon_deg


def x_to_lon_edges(x, z):
    tile_count = pow(2, z)
    unit = 360 / tile_count
    lon1 = -180 + x * unit
    lon2 = lon1 + unit
    return lon1, lon2


def mercator_to_lat(mercator_y):
    return degrees(atan(sinh(mercator_y)))


def y_to_lat_edges(y, z):
    tile_count = pow(2, z)
    unit = 1 / tile_count
    relative_y1 = y * unit
    relative_y2 = relative_y1 + unit
    lat1 = degrees(atan(sinh((pi * (1 - 2 * relative_y1)))))
    lat2 = degrees(atan(sinh((pi * (1 - 2 * relative_y2)))))
    return lat1, lat2


def tile_edges(x, y, z):
    lat1, lat2 = y_to_lat_edges(y, z)
    lon1, lon2 = x_to_lon_edges(x, z)
    return [lon1, lat1, lon2, lat2]


def georeference_tile(in_file, out_file, x, y, zoom):
    bounds = tile_edges(x, y, zoom)
    # filename, extension = os.path.splitext(path)
    Translate(out_file, in_file, outputSRS='EPSG:4326', outputBounds=bounds)


def slippy_tile_gen(in_geojson, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level, place_name):
    start = time.time()
    ts = time.time()
    geoms = []
    scheme = tiletanic.tileschemes.WebMercator()
    with fiona.open(in_geojson) as src:
        for rec in src:
            # Convert to web mercator, load as shapely geom.
            wm_geom = shape(transform_geom('EPSG:4326', 'EPSG:3857', rec['geometry']))

            if remove_holes:
                wm_geom = Polygon(wm_geom.exterior)
            geoms.append(wm_geom)
    # Find the covering.
    tiles = []
    for geom in geoms:
        tiles.extend(t for t in tiletanic.tilecover.cover_geometry(scheme, wm_geom, zoom))
    # Remove dupes if geoms overlapped.
    tiles = set(tiles)
    # Group by zip_zoom_level.
    zip_d = defaultdict(list)
    for t in tiles:
        zip_d[scheme.quadkey(t)[:zip_zoom_level]].append(t)
    # Note that at this stage we have all the XYZ tiles per zip_zoom_level.
    te = time.time()
    print(f'tiles created in {te - ts} seconds');

    ts = time.time()
    r_tiles = []
    id = 0
    for zzl in zip_d:
        for t in zip_d.get(zzl):
            bounds = tile_edges(t.x, t.y, t.z)
            r_tiles.append({
                'geometry': box(bounds[0], bounds[1], bounds[2], bounds[3]),
                'id': id,
                'x': t.x,
                'y': t.y,
                'zoom': t.z,
                'zip_zoom': zzl
            })
            id += 1
    result = gpd.GeoDataFrame(r_tiles).set_crs('epsg:4326')
    te = time.time()
    print(f'formatted as geoDataFrame in {te - ts} seconds');
    print('Begin Exporting Results to geojson file')
    ts = time.time()
    out_geojson = f"{place_name}.geojson"
    result.to_file(out_geojson, driver='GeoJSON')
    te = time.time()
    print(f"Exported to GeoJSON in {te - ts} seconds")
    end = time.time()  # End Clocking
    print(f"Processed {place_name} in {end - start} seconds")
    return result


if __name__ == "__main__":

    in_geojson = r'miami_beach_buffered.geojson'
    zoom = 21
    buffer_distance = None # Currently Not Working
    remove_holes = True
    zip_tiles = True # Attributes grid with necessary values for zipping using zipper.py
    zip_zoom_level = 13
    place_name = "miami_beach_tiles"

    slippy_tile_gen(in_geojson, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level, place_name)