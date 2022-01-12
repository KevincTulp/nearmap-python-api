import fiona
import geopandas as gpd
from shapely.geometry import mapping, Polygon
from zipfile import ZipFile
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from pathlib import Path
from os.path import splitext
from math import radians, asinh, tan, pi


#################
# Obtain CRS/SRS
################


def get_file_crs(in_file):
    with fiona.open(in_file, mode="r") as source:
        crs = source.crs.get('init').upper()
        return crs


def get_db_layer_crs(in_db, layer):
    with fiona.open(in_db, layer=layer.replace("main.", ""), mode="r") as source:
        crs = source.crs.get('init').upper()
        return crs

def lat_lon_to_slippy_coords(lat_deg, lon_deg, zoom):
    # From: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    lat_rad = radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - asinh(tan(lat_rad)) / pi) / 2.0 * n)
    return [xtile, ytile]

################
# File Reading
##############

def read_file_as_gdf(in_file, mask=None, to_crs='EPSG:4326'):
    supported_formats = [".shp", ".geojson"]
    supported_gdbs = [".gpkg", ".gdb"]
    f = Path(in_file)
    if f.is_dir():
        print(f"Detected input {in_file} as a Directory. Input must be a file or geodatabase/feature")
        exit()
    elif f.is_file():
        assert f.is_file(), f"Error: File {in_file} does not exist"
        assert f.suffix in supported_formats, f"Error: {in_file} format not a member of {supported_formats}"
        file_crs = get_file_crs(in_file)
        if file_crs is None or file_crs == to_crs:
            return gpd.read_file(f, mask=mask)
        else:
            return gpd.read_file(f, mask=mask).to_crs(to_crs)
    elif f.parents[0].suffix in supported_gdbs:
        gdb_name = f.parents[0]
        gdb_type = gdb_name.suffix
        layer_name = f.name
        get_db_layer_crs(gdb_name, layer_name)
        if gdb_type == ".gpkg":
            layer_name = layer_name.replace("main.", "")
            layer_crs = get_db_layer_crs(gdb_name, layer_name)
            if layer_crs is None or layer_crs == to_crs:
                return gpd.read_file(gdb_name, layer=layer_name, mask=mask)
            else:
                return gpd.read_file(gdb_name, layer=layer_name, mask=mask).to_crs(to_crs)
        elif gdb_type == ".gdb":
            print("Error: Esri GeoDatabase Format Not Supported")
            exit()
    else:
        print(f"Unable to detect file format for {in_file} or file format not supported")


################
# File Writing
###############


def write_gdf_to_file(gdf=None, output_file=None):
    output_file = Path(output_file).resolve().as_posix()
    print(output_file)
    supported_formats = [".shp", ".geojson"]
    supported_gdbs = [".gpkg", ".gdb"]
    if splitext(output_file)[1] in supported_formats:
        if output_file.endswith(".geojson"):
            return gdf.to_file(output_file, driver='GeoJSON')
        elif output_file.endswith(".shp"):
            return gdf.to_file(output_file)
    elif splitext(output_file)[1] in supported_gdbs:
        if output_file.endswith(".gpkg"):
            return gdf.to_file(output_file, layer="feature")
        elif output_file.endswith(".gdb"):
            print("Error: Esri GeoDatabase Format Not Supported")
            exit()
    elif splitext(split(output_file)[0])[1] in supported_gdbs:
        db, layer = split(output_file)
        db_format = splitext(db)[1]
        if db_format == ".gpkx":
            return gdf.to_file(Path(output_file), layer=layer)
        elif db_format == ".gdb":
            print("Error: Esri GeoDatabase Format Not Supported")
            exit()
    else:
        print(f"Error: Could not detect file format for {output_file} or format not supported")
        exit()


def shapely_polygon_to_shp(in_shapely_geom, crs, out_shapefile):
    # TODO: Support parsing more than one feature in list to a shapeile
    # TODO: Rename to shapely_geometry_writer or similar.
    # TODO: Support other formats and data types (line, point, polygon, multiline, multipolgon, multipoint) than just shape.
    # Define a polygon feature geometry with one attribute
    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int'},
    }

    # Write a new Shapefile
    with fiona.open(out_shapefile, 'w', crs=crs, driver='ESRI Shapefile', schema=schema) as c:
        c.write({
            'geometry': mapping(in_shapely_geom),
            'properties': {'id': 1},
        })
    return out_shapefile


def zip_dir(source, destination):
    base = Path(destination)
    name = base.stem
    file_format = base.suffix.strip(".")
    archive_from = Path(source).parents[0]
    archive_to = Path(source).name
    make_archive(name, file_format, archive_from, archive_to)
    move(base.name, base.parents[0].as_posix())


###################
# delete_geometry
#################


def delete_shapefile(in_shapefile):
    in_shp = Path(in_shapefile)
    shp_fmts = ['.shp', '.shx', '.dbf', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.atx', '.ixs', '.mxs', '.prj',
                '.xml', '.cpg']
    [in_shp.with_suffix(_).unlink() for _ in shp_fmts if in_shp.with_suffix(_).is_file()]


################
# Raster Data
##############


def get_raster_geom(in_raster, method=None, as_str=False):
    data = gdal.Open(in_raster, GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    xmin = geo_transform[0]
    ymax = geo_transform[3]
    xmax = xmin + geo_transform[1] * data.RasterXSize
    ymin = ymax + geo_transform[5] * data.RasterYSize
    ret_val = None
    if method in [None, "extent"]:
        if as_str:
            ret_val = f"{xmin} {ymin} {xmax} {ymax}"
        else:
            ret_val = [xmin, ymin, xmax, ymax]
    if method == "bounds":
        if as_str:
            f"{xmin} {ymin} {xmin} {ymax} {xmax} {ymax} {xmax} {ymin}"
        else:
            ret_val = [[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin]]
    if method == "polygon":
        if as_str:
            f"{xmin} {ymin} {xmin} {ymax} {xmax} {ymax} {xmax} {ymin} {xmin} {ymin}"
        else:
            ret_val = Polygon([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]])
    data = None
    return ret_val
