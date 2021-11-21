from pathlib import Path
from osgeo.gdal import Translate
from math import log, tan, radians, cos, atan, sinh, pi, degrees
from shapely.geometry import Polygon, box
import geopandas as gpd
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


def gen_slippy_grid_geoms(lat_min: float, lat_max: float, lon_min: float, lon_max: float, zoom: int):
    start = time.time()
    xmin, ymin = latlon_to_xy(lat_min, lon_min, zoom)
    xmax, ymax = latlon_to_xy(lat_max, lon_max, zoom)
    if xmax >= xmin:
        x_count = xmax - xmin
    elif xmax < xmin:
        x_count = xmin - xmax
    if ymax >= ymin:
        y_count = ymax - ymin
    elif ymax < ymin:
        y_count = ymin - ymax
    tiles = []
    count = 0
    for x in range(xmin, xmin + x_count + 1):
        for y in range(ymax, ymax + y_count + 1):
            bounds = tile_edges(x, y, zoom)
            tiles.append({
                'geometry': box(bounds[0], bounds[1], bounds[2], bounds[3]),
                'id': count,
                'x': x,
                'y': y,
                'zoom': zoom
            })
            count += 1
    end = time.time()  # End Clocking
    print(f"Generated Slippy Grid in {end - start} seconds")
    return gpd.GeoDataFrame(tiles).set_crs('epsg:4326')


def slippy_tile_gen(in_geojson, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level, place_name):
    start = time.time()
    with open(in_geojson) as f:
        data = load(f)
        slippy_gridz = []
        count = 0
        # for f in data.get('features'):
        gdf = gpd.read_file(in_geojson)
        #print(gdf.head())
        for index, row in gdf.iterrows():
            print(f"begin processing {place_name} feature {index}")
            AOI_Poly = row['geometry']

            # TODO Get this working
            if buffer_distance:
                # TODO: Requires detecting the UTM CRS and reprojecting data https://pyproj4.github.io/pyproj/stable/examples.html#find-utm-crs-by-latitude-and-longitude
                AOI_Poly = AOI_Poly.geometry.buffer(buffer_distance)
                # TODO: Then reproject to 'epsg:4326'
            if remove_holes:
                AOI_Poly = Polygon(list(AOI_Poly.exterior.coords))
            extent = AOI_Poly.bounds

            lon_min = min([extent[0], extent[2]])
            lon_max = max([extent[0], extent[2]])
            lat_min = min([extent[1], extent[3]])
            lat_max = max([extent[1], extent[3]])

            #print(lon_min, lon_max, lat_min, lat_max)
            the_slippy = gen_slippy_grid_geoms(lat_min, lat_max, lon_min, lon_max, zoom)

            aoi_poly_gdf = gpd.GeoDataFrame([{'geometry': AOI_Poly, 'id': 1}]).set_crs('epsg:4326')

            r = the_slippy.sjoin(aoi_poly_gdf, how="left")
            rdf = r[r.id_right.notnull()].drop(['id_left', 'id_right', 'index_right'], axis=1)
            if zip_tiles:
                zip_grid = gen_slippy_grid_geoms(lat_min, lat_max, lon_min, lon_max,
                                                 zoom=zip_zoom_level).drop(['zoom'], axis=1).rename(
                    columns={"x": "zip_x", "y": "zip_y"})

            result = rdf.sjoin(zip_grid, how="left").drop(['index_right', 'id'], axis=1).rename(columns={"id_1": "id"})
            result.to_file(f"{place_name}_{count}.geojson", driver='GeoJSON')
            count += 1
            end = time.time()  # End Clocking
            print(f"Processed {place_name} geometry # {index} in {end - start} seconds")


if __name__ == "__main__":

    in_geojson = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\nearmap\dev\NewOrleans.geojson'
    zoom = 21
    buffer_distance = None # Currently Not Working
    remove_holes = True
    zip_tiles = True # Attributes grid with necessary values for zipping using zipper.py
    zip_zoom_level = 13
    place_name = "NewOrleans_tiles.geojson"

    slippy_tile_gen(in_geojson, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level, place_name)
