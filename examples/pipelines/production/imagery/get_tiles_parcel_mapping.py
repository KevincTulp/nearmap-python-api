from nearmap.auth import get_api_key
from nearmap._api import _get_image
from nearmap import NEARMAP
from pathlib import Path, PurePath
from math import log, tan, radians, cos, atan, sinh, pi, degrees, floor, ceil
import fiona
from fiona.transform import transform_geom
from shapely.geometry import MultiPolygon, Polygon, box, shape, mapping
from shapely import ops
import pyproj
import tiletanic
import geopandas as gpd
from collections import defaultdict
import concurrent.futures
from zipfile import ZipFile
from shutil import rmtree, make_archive, move
from tqdm import tqdm
import time
import os
import sys
from os import cpu_count
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from PIL import Image

try:
    from osgeo_utils import gdal_merge
except ImportError:
    from osgeo.utils import gdal_merge

try:
    from ujson import load, dump, dumps
except ModuleNotFoundError:
    from json import load, dump, dumps

#gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')


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


def georeference_tile(in_file, out_file, x, y, zoom):
    bounds = tile_edges(x, y, zoom)
    # filename, extension = os.path.splitext(path)
    gdal.Translate(out_file, in_file, outputSRS='EPSG:4326', outputBounds=bounds)


def _create_folder(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _exception_info():
    exception_type, exception_object, exception_traceback = sys.exc_info()
    filename = exception_traceback.tb_frame.f_code.co_filename
    line_number = exception_traceback.tb_lineno
    return f'Exception type: {exception_type} | File name: {filename}, Line number: {line_number}'


def georeference_tiles(in_tiles, output_dir, scratch_dir, out_image_format, compression, jpeg_quality, image_basename,
                       geom, processing_method=None):
    tile_list = None
    tile_dir = None
    if isinstance(in_tiles, list):
        tile_list = in_tiles
        tile_dir = Path(tile_list[0]).parents[0]
    else:
        in_tiles = Path(in_tiles)
        if Path(in_tiles).is_dir() or Path(in_tiles).is_file():
            if Path(in_tiles).is_dir():
                tile_list = list(Path(in_tiles).iterdir())
                tile_dir = Path(tile_list[0]).parents[0]
            if Path(in_tiles).is_file():
                if Path(in_tiles).suffix in ['.jpg', '.png']:
                    tile_list = [in_tiles]
                    tile_dir = Path(in_tiles).parents[0]
                else:
                    tile_list = list(Path(in_tiles).iterdir())
                    tile_dir = Path(tile_list[0]).parents[0]
        else:
            print(f"Error: Check input formatting of '{in_tiles}'"
                  f" | Not properly formatted for 'georeference_tiles' proces")
    scratch_dir_georeg = Path(scratch_dir) / 'scratch_georeg'
    _create_folder(scratch_dir_georeg)

    georeferenced_tiles = []
    for f in tile_list:
        if f.is_file():
            x, y, z = f.stem.split("_")
            bounds = tile_edges(int(x), int(y), int(z))
            ext = f.suffix
            f_out = None
            if ext == ".jpg":
                # f_out = (scratch_dir_georeg / f'{f.name}').as_posix()
                # f_out = (scratch_dir_georeg / f'{f.stem}.tif').as_posix()
                f_out = (scratch_dir_georeg / f'{f.stem}.jpg').as_posix()
                # gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds, bandList=[1, 2, 3, "mask"])
                gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds, noData=0,
                               bandList=[1, 2, 3])
            elif ext == ".png":
                # f_out = (scratch_dir_georeg / f'{f.stem}.tif').as_posix()
                f_out = (scratch_dir_georeg / f'{f.stem}.tif').as_posix()
                # gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds)
                gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds, noData=255,
                               bandList=[1, 2, 3])
            georeferenced_tiles.append(f_out)

    def _merge_tiles(in_rasters, out_raster, out_image_format):
        # Only options - GTiff (the default) or HFA (Erdas Imagine)
        parameters = ['', '-o', out_raster, '-of', out_image_format, '-a_nodata', str(0), '-q'] + in_rasters
        gdal_merge.main(parameters)
        return out_raster

    formats = {'tif': {'gdal_name': 'GTiff', 'opacity_supported': True, 'compression_supported': True},
               'tiff': {'gdal_name': 'GTiff', 'opacity_supported': True, 'compression_supported': True},
               'jpg': {'gdal_name': 'JPG', 'opacity_supported': False, 'compression_supported': False},
               'png': {'gdal_name': 'PNG', 'opacity_supported': True, 'compression_supported': False}
               }

    scratch_tif_dir = scratch_dir / 'scratch_tif'
    _create_folder(scratch_tif_dir)
    out_raster = (scratch_tif_dir / f'{image_basename}.tif').as_posix()
    # try:
    in_raster = _merge_tiles(georeferenced_tiles, out_raster, formats.get('tif').get('gdal_name'))
    out_raster = (output_dir / f'{image_basename}.{out_image_format}').as_posix()
    _create_folder(output_dir)

    opacity_supported = formats.get(out_image_format).get('opacity_supported')
    compression_supported = formats.get(out_image_format).get('compression_supported')
    creationOptions = []
    wgs84_geom = None
    if compression_supported:
        creationOptions.append(f"COMPRESS={compression.upper()}")
        if compression.upper() == "JPEG" and out_image_format in ['tif', 'tiff']:
            creationOptions.append(f"JPEG_QUALITY={jpeg_quality}")
    if not compression_supported:
        if compression.upper() == "JPEG" and out_image_format in ["jpg", "jpeg"]:
            creationOptions.append(f"QUALITY={jpeg_quality}")

    if processing_method in ["mask", "bounds"]:
        wgs84 = pyproj.CRS('EPSG:4326')
        wgs84_pseudo = pyproj.CRS('EPSG:3857')

        project = pyproj.Transformer.from_crs(wgs84_pseudo, wgs84, always_xy=True).transform
        wgs84_geom = ops.transform(project, geom).intersection(get_raster_geom(in_raster, method="polygon"))

    if processing_method == "mask":
        shp = shapely_polygon_to_shp(in_shapely_geom=wgs84_geom, crs='EPSG:4326',
                                     out_shapefile=Path(scratch_tif_dir) / f'{image_basename}.shp')
        raster = gdal.Warp(out_raster, in_raster,
                           outputBounds=list(wgs84_geom.bounds),
                           outputBoundsSRS='EPSG:4326',
                           cutlineDSName=shp,
                           cropToCutline=True,
                           dstAlpha=opacity_supported,
                           creationOptions=creationOptions)

    elif processing_method == "bounds":
        raster = gdal.Warp(out_raster, in_raster,
                           outputBounds=list(wgs84_geom.bounds),
                           outputBoundsSRS='EPSG:4326',
                           dstAlpha=opacity_supported,
                           creationOptions=creationOptions)
    else:
        raster = gdal.Warp(out_raster, in_raster, dstAlpha=opacity_supported, creationOptions=creationOptions)

    # raster = gdal.Translate(out_raster, in_raster)
    rmtree(scratch_dir_georeg, ignore_errors=True)
    rmtree(scratch_tif_dir, ignore_errors=True)
    return raster

    '''
    except Exception as e:
        print(f'error: {image_basename} | failed to merge | {e} | {_exception_info()}')
        rmtree(scratch_dir_georeg, ignore_errors=True)
        return None
    '''


def shapely_polygon_to_shp(in_shapely_geom, crs, out_shapefile):
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


def zip_files(in_file_list, processing_folder, out_file_name):
    os.chdir(processing_folder)
    # TODO: Add output zipfile name
    with ZipFile(processing_folder / out_file_name, 'w') as zipF:
        for i in in_file_list:
            f = Path(i.get('file'))
            if f.is_file():
                try:
                    zipF.write(f.name)
                except FileNotFoundError as e:
                    print(e)

    os.chdir(Path(processing_folder).parents[0])
    out_file = Path()


def zip_dir(source, destination):
    base = Path(destination)
    name = base.stem
    file_format = base.suffix.strip(".")
    archive_from = Path(source).parents[0]
    archive_to = Path(source).name
    make_archive(name, file_format, archive_from, archive_to)
    move(base.name, base.parents[0].as_posix())


def _download_tiles(in_params, fid, out_manifest):

    url = in_params.get('url')
    path = Path(in_params.get('path')).resolve().as_posix()
    unique_id = in_params.get('id')
    fid_value = in_params.get(fid)
    ext = Path(path).suffix.replace(".", "")

    rotations = {"Vert": 0, "North": 0, "South": 180, "East": 270, "West": 90}

    def format_output_path(in_image, in_path):
        format = in_image.get_format_mimetype()
        if "jpeg" in format:
            out_path = Path(in_path.replace(".img", ".jpg")).resolve().as_posix()
        else:
            out_path = Path(in_path.replace(".img", ".png")).resolve().as_posix()

        return out_path
    try:
        if "North" in url or "Vert" in url:
            image = _get_image(url=url, out_format=ext, out_image=path, rate_limit_mode="slow", quiet=True)
        elif "South" in url:
            image_bytes = Image.open(_get_image(url=url, out_format=ext, out_image="bytes", rate_limit_mode="slow",
                                                quiet=True))
            image_rotated = image_bytes.rotate(rotations.get("South"))
            image = format_output_path(image_bytes, path)
            image_rotated.save(image)
            del image_bytes, image_rotated
        elif "East" in url:
            image_bytes = Image.open(_get_image(url=url, out_format=ext, out_image="bytes", rate_limit_mode="slow",
                                                quiet=True))
            image_rotated = image_bytes.rotate(rotations.get("East"))
            image = format_output_path(image_bytes, path)
            image_rotated.save(image)
            del image_bytes, image_rotated
        elif "West" in url:
            image_bytes = Image.open(_get_image(url=url, out_format=ext, out_image="bytes", rate_limit_mode="slow",
                                                quiet=True))
            image_rotated = image_bytes.rotate(rotations.get("West"))
            image = format_output_path(image_bytes, path)
            image_rotated.save(image)
            del image_bytes, image_rotated
    except Exception as e:
        print(f"Error: Error downloading image for: {unique_id} | {fid_value} | {path} | {_exception_info()}")
        image = None
    if image is None:
        print(f"Error: Error downloading image for: {unique_id} | {fid_value} | {path}")
    elif not Path(image).is_file():
        print(f"Error: Error with image path: {unique_id} | {fid_value} | {path}")
    if not out_manifest:
        m = dict()
        m['id'] = unique_id
        m[fid] = fid_value
        m['file'] = image
        return m
    if out_manifest:
        x = in_params.get('x')
        y = in_params.get('y')
        z = in_params.get('zoom')
        bounds = tile_edges(x, y, z)
        m = dict()
        m['geometry'] = box(bounds[0], bounds[1], bounds[2], bounds[3])
        m['id'] = unique_id
        m[fid] = fid_value
        m['x'] = in_params.get('x')
        m['y'] = in_params.get('y')
        m['zoom'] = in_params.get('zoom')
        m['success'] = True
        m['file'] = image
        return m


def _return_existing(in_params, image, fid, out_manifest):
    url = in_params.get('url')
    path = in_params.get('path')
    unique_id = in_params.get('id')
    fid_value = in_params.get(fid)
    ext = Path(path).suffix.replace(".", "")
    if not out_manifest:
        m = dict()
        m['id'] = unique_id
        m[fid] = fid_value
        m['file'] = image
        return m
    if out_manifest:
        x = in_params.get('x')
        y = in_params.get('y')
        z = in_params.get('zoom')
        try:
            bounds = Polygon(gdal.Info(image, format='json').get('wgs84Extent').get('coordinates')[0])
        except Exception as e:
            print(f"error: {fid_value} | {e} | {_exception_info()}")
            bounds = Polygon([[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])
        m = dict()
        m['geometry'] = bounds
        m['id'] = unique_id
        m[fid] = fid_value
        m['x'] = in_params.get('x')
        m['y'] = in_params.get('y')
        m['zoom'] = in_params.get('zoom')
        m['success'] = True
        m['file'] = image
        return m


def _process_tiles(nearmap, project_folder, tiles_folder, feature, fid, out_image_format, compression, jpeg_quality,
                   processing_method, out_manifest, num_threads, surveyid, tileResourceType, tertiary, since, until,
                   mosaic, include, exclude, rate_limit_mode):
    fid_value = feature.get(fid)
    unique_id = feature.get('id')
    geom = feature.get('geom')
    out_raster = Path(project_folder) / f'{fid_value}.{out_image_format}'
    if Path(out_raster).is_file():
        temp = dict()
        temp['id'] = unique_id
        temp[fid] = fid_value
        temp['url'] = None
        temp['path'] = out_raster
        temp['x'] = 0
        temp['y'] = 0
        temp['zoom'] = 0
        results = _return_existing(temp, out_raster, fid, out_manifest)
        return [results]
    else:
        jobs = []
        my_tiles_folder = Path(tiles_folder) / f'{fid_value}'
        _create_folder(my_tiles_folder)
        api_key = nearmap.api_key
        out_format = 'img'
        if surveyid:
            contentType = tileResourceType
            url_template = nearmap.tileSurveyV3(surveyid, contentType, z=0, x=0, y=2, out_format=out_format,
                                                out_image='.img', rate_limit_mode="slow", return_url=True)
        if not surveyid:
            url_template = nearmap.tileV3(tileResourceType=tileResourceType, z=0, x=1, y=2, out_format=out_format,
                                          out_image='.img', tertiary=tertiary, since=since, until=until, mosaic=mosaic,
                                          include=include, exclude=exclude, rate_limit_mode=rate_limit_mode,
                                          return_url=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            for t in feature.get('tiles'):
                z = t.z
                x = t.x
                y = t.y
                path = my_tiles_folder / f'{t.x}_{t.y}_{t.z}.img'
                url = eval(url_template)
                temp = dict()
                temp['id'] = unique_id
                temp[fid] = fid_value
                temp['url'] = url
                temp['path'] = path
                temp['x'] = t.x
                temp['y'] = t.y
                temp['zoom'] = t.z
                jobs.append(executor.submit(_download_tiles, temp, fid, out_manifest))

        # TODO: Zip the tiles that were downloaded.
        results = []
        for job in jobs:
            result = job.result()
            results.append(result)
        if out_image_format.lower() == 'zip':
            zip_dir(my_tiles_folder, project_folder / f'{fid_value}.zip')
            rmtree(my_tiles_folder, ignore_errors=True)
        elif out_image_format is None:
            pass
        else:
            my_scratch_folder = tiles_folder / f'scratch_{fid_value}'
            _create_folder(my_scratch_folder)
            georeference_tiles(my_tiles_folder, project_folder, my_scratch_folder, out_image_format, compression,
                               jpeg_quality, image_basename=fid_value, geom=geom, processing_method=processing_method)
            rmtree(my_tiles_folder, ignore_errors=True)
            rmtree(my_scratch_folder, ignore_errors=True)
        return results


def geom_bounds_poly(in_geom):
    xmin, ymin, xmax, ymax = in_geom.bounds
    return Polygon([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]])


def tile_downloader(nearmap, input_geojson, fid, skip_duplicate_fid, output_dir, out_manifest, zoom, download_method,
                    buffer_distance, remove_holes, out_image_format, compression=None, jpeg_quality=75,
                    processing_method=None, surveyid=None, tileResourceType='Vert', tertiary=None, since=None,
                    until=None, mosaic=None, include=None, exclude=None, rate_limit_mode="slow", max_cores=None,
                    max_threads=None):

    input_geojson = Path(input_geojson).resolve()
    output_dir = Path(output_dir).resolve()

    # from shapely.geometry import multipolygon, polygon
    supported_formats = [".geojson"]
    assert input_geojson.is_file(), f"Error: in_geojson {input_geojson} is not a file"
    assert input_geojson.suffix in supported_formats, f"Error: 'input_geojson' {input_geojson} format not in " \
                                                      f"{supported_formats}"
    assert not output_dir.is_file(), f"Error: 'output_dir' cannot be a file... must be a folder/directory"

    if not skip_duplicate_fid:
        with fiona.open(input_geojson) as src:
            l = list()
            for i in tqdm(src):
                v = i.get('properties').get(fid)
                if v in l:
                    print({'status': f"Error: Duplicate FID's detected in '{fid}'"
                                     f". Resolve before processing or script will fail"})
                    exit()
                l.append(v)

    project_folder = output_dir
    _create_folder(project_folder)
    tiles_folder = project_folder / 'tiles'
    start = time.time()
    ts = time.time()
    geoms = []
    scheme = tiletanic.tileschemes.WebMercator()
    count = 0
    features = list()
    with fiona.open(input_geojson) as src:
        src_crs = src.crs.get('init').upper()
        l = list()
        num_records = len(list(src))
        for rec in tqdm(src, desc="Preparing Records for Processing..."):
            feature = dict()
            tiles = []
            feature['id'] = count
            v = rec.get('properties').get(fid)
            feature[fid] = v
            if v in l:
                pass
            else:
                l.append(v)
                geom = None
                if src_crs != 'EPSG:3857':
                    geom = shape(transform_geom('EPSG:4326', 'EPSG:3857', rec.get('geometry')))
                else:
                    geom = shape(rec.get('geometry'))
                if buffer_distance:
                    geom = geom.buffer(buffer_distance, cap_style=3, join_style=2)
                geom_type = geom.geom_type
                if geom_type == 'MultiPolygon':
                    g_list = list()
                    if download_method.lower() == 'bounds':
                        g_bounds = geom_bounds_poly(geom)
                        tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, g_bounds, zoom)])
                        feature['geom'] = g_bounds
                        del g_bounds
                    elif download_method.lower() == 'bounds_per_feature':
                        g_list = list()
                        geoms = geom.geoms
                        for g in geoms:
                            g_bounds = geom_bounds_poly(g)
                            tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, g_bounds, zoom)])
                            g_list.append(g_bounds)
                        feature['geom'] = MultiPolygon(geoms)
                        del g_list
                    elif remove_holes:
                        g_list = list()
                        geoms = geom.geoms
                        for g in geoms:
                            g_ext = g.exterior
                            tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, g_ext, zoom)])
                            g_list.append(g_ext)
                        feature['geom'] = MultiPolygon(geoms)
                        del g_list
                    else:  # If retain 'geometry'
                        geoms = geom.geoms
                        for g in geoms:
                            tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, g, zoom)])
                        feature['geom'] = geom
                elif geom_type == 'Polygon':
                    if download_method.lower() in ['bounds', 'bounds_per_feature']:
                        tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, geom_bounds_poly(geom),
                                                                                    zoom)])
                        feature['geom'] = geom
                    elif remove_holes:
                        tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, Polygon(geom.exterior),
                                                                                    zoom)])
                        feature['geom'] = geom
                    else: # If retain 'geometry'
                        tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, Polygon(geom),
                                                                                    zoom)])
                        feature['geom'] = geom
                else:
                    print(f'{geom_type} is currently not supported')
                    exit()
                # Remove dupes if geoms overlapped.
                tiles = list(set(tiles))
                feature['tiles'] = tiles
                count += 1
                features.append(feature)
                del feature, tiles
        print({'status': f'Processing {len(l)} of {num_records} Records | Skipping {num_records-len(l)} '
                         f'"{fid}" duplicates'})
        del l
    te = time.time()
    ts = time.time()
    r_tiles = []
    time.sleep(0.1)  # Sleep Temporarily to ensure previous stats are printed

    system_cores = cpu_count()
    if max_cores:
        if max_cores > system_cores:
            print({'status': f"User Input {max_cores} 'max_cores' > system cpu cores. Reverting to {system_cores} 'max_cores'"})
            max_cores = system_cores
        elif max_cores < system_cores:
            print({'status': f"User Input {max_cores} 'max_cores' < {system_cores} available system cpu cores... continuing process"})
    else:
        max_cores = system_cores
    threads_per_core = 5
    num_cores = None
    num_threads = None
    #print(f'Threads: {max_threads} | zip_d: {len(zip_d)}')
    num_features = len(features)
    if num_features > max_cores:
        num_cores = max_cores
        if max_threads:
            num_threads = max_threads / num_cores
        else:
            num_threads = threads_per_core
        print({'status': f'Downloading Tiles using {num_cores} Cores & {num_threads} Threads Per Core'})
    else:
        num_cores = num_features
        if max_threads:
            num_threads = max_threads / num_cores
        else:
            num_threads = ceil((system_cores * threads_per_core) / num_cores)
        print({'status': f'Processing tiles using {num_cores} Cores | Downloading Tiles using {num_threads} Threads Per Core'})
    time.sleep(0.1)

    with tqdm(total=num_features) as progress:
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
            jobs = []
            for feature in features:
                jobs.append(executor.submit(_process_tiles, nearmap, project_folder, tiles_folder, feature, fid,
                                            out_image_format, compression, jpeg_quality, processing_method,
                                            out_manifest, num_threads, surveyid, tileResourceType, tertiary, since,
                                            until, mosaic, include, exclude, rate_limit_mode))
            for job in jobs:
                result = job.result()
                if out_manifest:
                    r_tiles.extend(result)
                progress.update()
    te = time.time()
    print({'status': f'Downloaded and Zipped Tiles in {te - ts} seconds'})
    del features
    if out_manifest:
        ts = time.time()
        print({'status': 'Begin Loading Manifest to GeoDataFrame'})
        # print(f'Begin Loading Manifest to GeoDataFrame')
        result = gpd.GeoDataFrame(r_tiles).set_crs('epsg:4326')
        te = time.time()
        print({'status': f'Loaded Manifest as GeoDataFrame in {te - ts} seconds'})
        print({'status': 'Begin Exporting Results to geojson file'})
        ts = time.time()
        manifest_file = project_folder / "manifest.geojson"
        result.to_file(manifest_file, driver='GeoJSON')
        te = time.time()
        print({'status': f"Exported to GeoJSON in {te - ts} seconds"})
        ts = time.time()
        print({'status': 'Begin Exporting Result Extents to geojson file'})
        manifest_extents_file = project_folder / "manifest_extents.geojson"
        result.dissolve(by=fid).drop(columns="file", axis=1).to_file(manifest_extents_file, driver='GeoJSON')
        te = time.time()
        print({'status': f"Exported to GeoJSON in {te - ts} seconds"})

    rmtree(tiles_folder, ignore_errors=True)
    end = time.time()  # End Clocking
    print({'status': f"Processed in {end - start} seconds"})


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here
    nearmap = NEARMAP(api_key)

    input_geojson = r'../test_data/parcels_with_pools.geojson'  #r'../../../nearmap/unit_tests/TestData/Parcels_Vector/JSON/Parcels.geojson'
    fid = "property_id"
    #fid = 'HCAD_NUM'  # Unique Feature ID for downloading/processing
    skip_duplicate_fid = True
    output_dir = r'C:/ok'
    zoom = 21  # Nearmap imagery zoom level
    download_method = 'bounds'  # 'bounds', 'bounds_per_feature', or 'geometry'
    buffer_distance = 0  # Buffer Distance in Meters
    remove_holes = True  # Remove holes within polygons
    out_image_format = 'jpg'  # supported: 'jpg', 'tif', 'png'
    compression = 'JPEG'  # [JPEG/LZW/PACKBITS/DEFLATE/CCITTRLE/CCITTFAX3/CCITTFAX4/LZMA/ZSTD/LERC/LERC_DEFLATE/LERC_ZSTD/WEBP/JXL/NONE]
    jpeg_quality = 100  # Only used if using JPEG Compression range[1-100]..
    processing_method = None  # "mask" "bounds" or None <-- Enables Masking or clipping of image to input polygon
    out_manifest = True  # Output a manifest of data extracted

    ###############################
    # Survey Specific User Params
    #############################

    surveyid = None  # Optional for calling a specfic survey...
    tileResourceType = 'Vert'  # Currently only 'Vert' and 'North' are supported
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None
    rate_limit_mode = 'slow'

    tile_downloader(nearmap, input_geojson, fid, skip_duplicate_fid, output_dir, out_manifest, zoom, download_method,
                    buffer_distance, remove_holes, out_image_format, compression, jpeg_quality, processing_method,
                    surveyid, tileResourceType, tertiary, since, until, mosaic, include, exclude, rate_limit_mode)
