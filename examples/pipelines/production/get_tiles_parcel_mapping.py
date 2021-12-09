from nearmap.auth import get_api_key
from nearmap._api import _get_image
from nearmap import NEARMAP
from pathlib import Path
from osgeo.gdal import Translate
from math import log, tan, radians, cos, atan, sinh, pi, degrees, floor, ceil
import fiona
from fiona.transform import transform_geom
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely import ops
import tiletanic
import geopandas as gpd
from collections import defaultdict
import concurrent.futures
from zipfile import ZipFile
from shutil import rmtree, make_archive, move
from tqdm import tqdm
import time
import os
from os import cpu_count
from osgeo.gdal import Translate
try:
    from osgeo_utils import gdal_merge
except ImportError:
    from osgeo.utils import gdal_merge

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


def _create_folder(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def georeference_tiles(in_tiles, output_dir, scratch_dir, out_image_format, image_basename):
    tile_list = None
    tile_dir = None
    if isinstance(in_tiles, list):
        tile_list = in_tiles
        tile_dir = Path(tile_list[0]).parents[0]
    elif isinstance(in_tiles, str):
        if in_tiles.endswith('.jpg') or in_tiles.endswith('.png'):
            tile_list = [in_tiles]
            tile_dir = Path(in_tiles).parents[0]
        else:
            tile_list = list(Path(in_tiles).iterdir())
            tile_dir = Path(tile_list[0]).parents[0]
    else:
        print(f"Error: Check input formatting of '{in_tiles}' | Not properly formatted for 'georeference_tiles' process")

    scratch_dir_georeg = f'{scratch_dir}\\scratch_georeg'
    _create_folder(scratch_dir_georeg)

    georeferenced_tiles = []
    for f in tile_list:
        x, y, z = f.stem.split("_")
        bounds = tile_edges(int(x), int(y), int(z))
        f_out = f'{scratch_dir_georeg}\\{f.name}'
        Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds)
        georeferenced_tiles.append(f_out)

    def _merge_tiles(in_rasters, out_raster, out_image_format):
        # Only options - GTiff (the default) or HFA (Erdas Imagine)
        parameters = ['', '-o', out_raster, '-of', out_image_format, '-q'] + in_rasters
        gdal_merge.main(parameters)
        return out_raster

    formats = {'tif': {'gdal_name': 'GTiff'},
               'tiff': {'gdal_name': 'GTiff'},
               'jpg': {'gdal_name': 'JPG'},
               'png': {'gdal_name': 'PNG'}
               }
    if out_image_format.lower() in ['tif', 'tiff', 'bil']:
        _create_folder(output_dir)
        out_raster = f'{output_dir}\\{image_basename}.{out_image_format}'
        raster = _merge_tiles(georeferenced_tiles, out_raster, formats.get(out_image_format).get('gdal_name'))
        rmtree(scratch_dir_georeg)
        return raster
    else:
        scratch_tif_dir = f'{scratch_dir}\\scratch_tif'
        _create_folder(scratch_tif_dir)
        out_raster = f'{scratch_tif_dir}\\{image_basename}.tif'
        in_raster = _merge_tiles(georeferenced_tiles, out_raster, formats.get('tif').get('gdal_name'))
        out_raster = f'{output_dir}\\{image_basename}.{out_image_format}'
        _create_folder(output_dir)
        raster = Translate(out_raster, in_raster)
        rmtree(scratch_dir_georeg)
        rmtree(scratch_tif_dir)
        return raster


def zip_files(in_file_list, processing_folder, out_file_name):
    os.chdir(processing_folder)
    # TODO: Add output zipfile name
    with ZipFile(f"{processing_folder}\\{out_file_name}", 'w') as zipF:
        for i in in_file_list:
            f = Path(i.get('file'))
            if f.is_file():
                try:
                    zipF.write(f.name)
                except FileNotFoundError as e:
                    print(e)

    os.chdir(Path(processing_folder).parents[0])
    out_file = Path()
    #shutil.move(src, dst)


def zip_dir(source, destination):
    base = Path(destination)
    name = base.stem
    file_format = base.suffix.strip(".")
    archive_from = Path(source).parents[0]
    archive_to = Path(source).name
    #print(source, destination, archive_from, archive_to)
    make_archive(name, file_format, archive_from, archive_to)
    #print(base.name, base.parents)
    move(base.name, base.parents[0].as_posix())


def _download_tiles(in_params, fid, out_manifest):
    url = in_params.get('url')
    path = in_params.get('path')
    unique_id = in_params.get('id')
    fid_value = in_params.get(fid)
    ext = Path(path).suffix.replace(".", "")
    # print(url, ext, path)
    image = _get_image(url=url, out_format=ext, out_image=path, rate_limit_mode="slow")
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


def _process_tiles(nearmap, project_folder, tiles_folder, feature, fid, out_image_format, out_manifest, num_threads,
                   surveyid, tileResourceType, tertiary, since, until, mosaic, include, exclude, rate_limit_mode):
    jobs = []
    id = feature.get('id')
    fid_value = feature.get(fid)
    my_tiles_folder = f'{tiles_folder}/{fid_value}'
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
                                     include=include, exclude=exclude, rate_limit_mode=rate_limit_mode, return_url=True)

    with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
        for t in feature.get('tiles'):
            z = t.z
            x = t.x
            y = t.y
            path = f'{my_tiles_folder}\\{t.x}_{t.y}_{t.z}.img'
            url = eval(url_template)
            temp = dict()
            temp['id'] = id
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
    # time.sleep(0.5)
    if out_image_format.lower() == 'zip':
        zip_dir(my_tiles_folder, f'{project_folder}/{fid_value}.zip')
        #zip_files(in_file_list=results, processing_folder=tiles_folder, out_file_name=f"{zzl}.zip")
        rmtree(my_tiles_folder)
    elif out_image_format is None:
        pass
    else:
        my_scratch_folder = f'{tiles_folder}/scratch_{fid_value}'
        _create_folder(my_scratch_folder)
        georeference_tiles(my_tiles_folder, project_folder, my_scratch_folder, out_image_format, image_basename=fid_value)
        rmtree(my_tiles_folder)
        rmtree(my_scratch_folder)
    return results


def geom_bounds_poly(in_geom):
    xmin, ymin, xmax, ymax = in_geom.bounds
    return Polygon([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]])


def tile_downloader(nearmap, input_geojson, fid, output_dir, out_manifest, zoom, download_method, buffer_distance,
                    remove_holes, out_image_format, surveyid=None, tileResourceType='Vert',
                    tertiary=None, since=None, until=None, mosaic=None, include=None, exclude=None,
                    rate_limit_mode="slow", max_cores=None, max_threads=None):
    from shapely.geometry import multipolygon, polygon
    assert Path(input_geojson).suffix == ".geojson", f"Error: 'input_geojson' {input_geojson} is not of type '.geojson'"
    project_folder = f'{output_dir}'
    _create_folder(project_folder)
    tiles_folder = f'{project_folder}/tiles'
    start = time.time()
    ts = time.time()
    geoms = []
    scheme = tiletanic.tileschemes.WebMercator()
    count = 0
    features = list()
    with fiona.open(input_geojson) as src:
        num_records = len(list(src))
        #print(f'Number of Records: {num_records}')
        for rec in tqdm(src, desc="Preparing Records for Processing..."):
            feature = dict()
            tiles = []
            feature['id'] = count
            feature[fid] = rec.get('properties').get(fid)
            geom = shape(transform_geom('EPSG:4326', 'EPSG:3857', rec.get('geometry')))
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
                else: # If retain 'geometry'
                    geoms = geom.geoms
                    for g in geoms:
                        tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, g, zoom)])
                    feature['geom'] = geom
            elif geom_type == 'Polygon':
                if download_method.lower() in ['bounds', 'bounds_per_feature']:
                    tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, geom_bounds_poly(geom),
                                                                                zoom)])
                elif remove_holes:
                    tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, Polygon(geom.exterior),
                                                                                zoom)])
                else: # If retain 'geometry'
                    tiles.extend([i for i in tiletanic.tilecover.cover_geometry(scheme, Polygon(geom),
                                                                                zoom)])
            else:
                print(f'{geom_type} is currently not supported')
                exit()
            # Remove dupes if geoms overlapped.
            tiles = list(set(tiles))
            feature['tiles'] = tiles
            count += 1
            features.append(feature)
            del feature, tiles
    te = time.time()
    ts = time.time()
    r_tiles = []
    time.sleep(0.1)  # Sleep Temporarily to ensure previous stats are printed

    system_cores = cpu_count()
    if max_cores:
        if max_cores > system_cores:
            print(f"User Input {max_cores} 'max_cores' > system cpu cores. Reverting to {system_cores} 'max_cores'")
            max_cores = system_cores
        elif max_cores < system_cores:
            print(f"User Input {max_cores} 'max_cores' < {system_cores} available system cpu cores... continuing process")
    else:
        max_cores = system_cores
    num_cores = None
    num_threads = None
    #print(f'Threads: {max_threads} | zip_d: {len(zip_d)}')
    num_features = len(features)
    if num_features > max_cores:
        num_cores = max_cores
        if max_threads:
            num_threads = max_threads / num_cores
        else:
            num_threads = 5
        print({'status': f'Downloading Tiles using {num_cores} Cores & {num_threads} Threads Per Core'})
    else:
        num_cores = num_features
        if max_threads:
            num_threads = max_threads / num_cores
        else:
            num_threads = ceil((system_cores * 5) / num_cores)
        print({'status': f'Processing tiles using {num_cores} Cores | Downloading Tiles using {num_threads} Threads Per Core'})
    time.sleep(0.1)

    with tqdm(total=num_features) as progress:
        with concurrent.futures.ProcessPoolExecutor(num_cores) as executor:
            jobs = []
            for feature in features:
                jobs.append(executor.submit(_process_tiles, nearmap, project_folder, tiles_folder, feature, fid,
                                            out_image_format, out_manifest, num_threads, surveyid, tileResourceType,
                                            tertiary, since, until, mosaic, include, exclude, rate_limit_mode))
            for job in jobs:
                result = job.result()
                if out_manifest:
                    r_tiles.extend(result)
                progress.update()
    te = time.time()
    print({'status': f'Downloaded and Zipped Tiles in {te - ts} seconds'});
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
        result.to_file(f"{project_folder}\\manifest.geojson", driver='GeoJSON')
        te = time.time()
        print({'status': f"Exported to GeoJSON in {te - ts} seconds"})

    rmtree(tiles_folder)
    end = time.time()  # End Clocking
    print({'status': f"Processed in {end - start} seconds"})


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here
    nearmap = NEARMAP(api_key)

    input_geojson = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\nearmap\unit_tests\TestData\Parcels_Vector\JSON\Parcels.geojson'
    fid = 'FID' # Unique Feature ID for downloading/processing
    output_dir = r'C:\output'
    zoom = 21 # Nearmap imagery zoom level
    download_method = 'bounds' # 'bounds', 'bounds_per_feature', or 'geometry'
    buffer_distance = 1  # Buffer Distance in Meters
    remove_holes = True # Remove holes within polygons
    out_image_format = 'jpg' # supported: 'jpg', 'tif', 'png'
    out_manifest = True # Output a manifest of data extracted

    ###############################
    # Survey Specific User Params
    #############################

    surveyid = None # Optional for calling a spefic survey...
    tileResourceType = 'Vert' # Currently only 'Vert' and 'North' are supported
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None
    rate_limit_mode = 'slow'

    tile_downloader(nearmap, input_geojson, fid, output_dir, out_manifest, zoom, download_method, buffer_distance,
                    remove_holes, out_image_format, surveyid, tileResourceType, tertiary, since, until, mosaic, include,
                    exclude, rate_limit_mode)
