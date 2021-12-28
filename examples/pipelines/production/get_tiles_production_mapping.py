from nearmap.auth import get_api_key
from nearmap._api import _get_image
from nearmap import NEARMAP
from pathlib import Path
from osgeo.gdal import Translate
from math import log, tan, radians, cos, atan, sinh, pi, degrees, floor, ceil
import fiona
from fiona.transform import transform_geom
from shapely.geometry import Polygon, box, shape
from shapely import ops
import tiletanic
import geopandas as gpd
from collections import defaultdict
import concurrent.futures
from zipfile import ZipFile
from shutil import rmtree, make_archive, move
from tqdm import tqdm
import time
import sys
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


def _exception_info():
    exception_type, exception_object, exception_traceback = sys.exc_info()
    filename = exception_traceback.tb_frame.f_code.co_filename
    line_number = exception_traceback.tb_lineno
    return f'Exception type: {exception_type} | File name: {filename}, Line number: {line_number}'


def georeference_tiles(in_tiles, output_dir, scratch_dir, out_image_format, image_basename):
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
        x, y, z = f.stem.split("_")
        bounds = tile_edges(int(x), int(y), int(z))
        f_out = (scratch_dir_georeg / f'{f.name}').as_posix()
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
        out_raster = output_dir / f'{image_basename}.{out_image_format}'
        raster = _merge_tiles(georeferenced_tiles, out_raster.as_posix(), formats.get(out_image_format).get('gdal_name'))
        rmtree(scratch_dir_georeg, ignore_errors=True)
        return raster
    else:
        scratch_tif_dir = scratch_dir / 'scratch_tif'
        _create_folder(scratch_tif_dir)
        out_raster = (scratch_tif_dir / f'{image_basename}.tif').as_posix()
        try:
            in_raster = _merge_tiles(georeferenced_tiles, out_raster, formats.get('tif').get('gdal_name'))
            out_raster = (output_dir / f'{image_basename}.{out_image_format}').as_posix()
            _create_folder(output_dir)
            raster = Translate(out_raster, in_raster)
            rmtree(scratch_dir_georeg)
            rmtree(scratch_tif_dir)
            return raster
        except Exception as e:
            print(f'error: {image_basename} | failed to merge | {e} | {_exception_info()}')
            rmtree(scratch_dir_georeg, ignore_errors=True)
            return None


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


def _download_tiles(in_params, out_manifest):
    url = in_params.get('url')
    path = in_params.get('path')
    fid = in_params.get('id')
    ext = Path(path).suffix.replace(".", "")
    # print(url, ext, path)
    image = _get_image(url=url, out_format=ext, out_image=path.as_posix(), rate_limit_mode="slow")
    if not out_manifest:
        m = dict()
        m['id'] = fid
        m['file'] = image
        return m
    if out_manifest:
        x = in_params.get('x')
        y = in_params.get('y')
        z = in_params.get('zoom')
        bounds = tile_edges(x, y, z)
        m = dict()
        m['geometry'] = box(bounds[0], bounds[1], bounds[2], bounds[3])
        m['id'] = fid
        m['x'] = in_params.get('x')
        m['y'] = in_params.get('y')
        m['zoom'] = in_params.get('zoom')
        m['zip_zoom'] = in_params.get('zip_zoom')
        m['success'] = True
        m['file'] = image
        return m


def _process_tiles(nearmap, project_folder, tiles_folder, zzl, zip_d, out_image_format, out_manifest, num_threads,
                   surveyid, tileResourceType, tertiary, since, until, mosaic, include, exclude, rate_limit_mode):
    fid = 0
    jobs = []
    zzl_tiles_folder = tiles_folder / f'{zzl}'
    _create_folder(zzl_tiles_folder)

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

    with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
        for t in zip_d.get(zzl):
            z = t.z
            x = t.x
            y = t.y
            path = zzl_tiles_folder / f'{t.x}_{t.y}_{t.z}.img'
            url = eval(url_template)
            temp = dict()
            temp['id'] = fid
            temp['url'] = url
            temp['path'] = path
            temp['x'] = t.x
            temp['y'] = t.y
            temp['zoom'] = t.z
            temp['zip_zoom'] = zzl
            jobs.append(executor.submit(_download_tiles, temp, out_manifest))
            fid += 1
    # TODO: Zip the tiles that were downloaded.
    results = []
    for job in jobs:
        result = job.result()
        results.append(result)
    # time.sleep(0.5)
    if out_image_format.lower() == 'zip':
        zip_dir(zzl_tiles_folder, project_folder / f'{zzl}.zip')
        #zip_files(in_file_list=results, processing_folder=tiles_folder, out_file_name=f"{zzl}.zip")
        rmtree(zzl_tiles_folder)
    elif out_image_format is None:
        pass
    else:
        zzl_scratch_folder = tiles_folder / f'scratch_{zzl}'
        _create_folder(zzl_scratch_folder)
        georeference_tiles(zzl_tiles_folder, project_folder, zzl_scratch_folder, out_image_format, image_basename=zzl)
        rmtree(zzl_tiles_folder)
        rmtree(zzl_scratch_folder)
    return results


def tile_downloader(nearmap, input_dir, output_dir, out_manifest, zoom, buffer_distance, remove_holes, out_image_format,
                    group_zoom_level, processing_method=None, surveyid=None, tileResourceType='Vert', tertiary=None,
                    since=None, until=None, mosaic=None, include=None, exclude=None, rate_limit_mode="slow",
                    max_cores=None, max_threads=None):

    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve()

    assert input_dir.is_dir(), f"Error: 'input_dir' {input_dir}is not a folder/directory"
    assert not output_dir.is_file(), f"Error: 'output_dir' {output_dir} cannot be a file... must be a folder/directory"

    supported_formats = ['.geojson']
    files = tqdm([f for f in list(Path(input_dir).iterdir()) if f.suffix in supported_formats])
    in_geojson = None
    for file in files:
        if file.suffix == ".geojson":
            in_geojson = file
        files.set_description(f"Processing {file.name}")
        name_string = Path(in_geojson).stem.replace("_Source", "")
        state_abbrev = name_string.split("_")[0]
        place_name = f'{name_string.split("_")[1]}_{name_string.split("_")[2]}'
        project_folder = output_dir / state_abbrev / place_name
        _create_folder(project_folder)
        tiles_folder = project_folder / 'tiles'
        files.set_postfix({'status': 'Generating Tile Grid'})
        start = time.time()
        ts = time.time()
        geoms = []
        scheme = tiletanic.tileschemes.WebMercator()
        in_geojson = Path(in_geojson)
        with fiona.open(in_geojson) as src:
            for rec in src:
                # Convert to web mercator, load as shapely geom.
                print(rec.get('geometry'))
                wm_geom = shape(transform_geom('EPSG:4326', 'EPSG:3857', rec.get('geometry')))
                print(wm_geom)
                if buffer_distance or buffer_distance != 0:
                    wm_geom = wm_geom.buffer(buffer_distance, cap_style=3, join_style=2)
                    print(wm_geom)
                if remove_holes:
                    wm_geom = Polygon(wm_geom.exterior)
                    print(wm_geom)
                geoms.append(wm_geom)
                #exit()
        # Find the covering.
        tiles = []
        for geom in geoms:
            tiles.extend(t for t in tiletanic.tilecover.cover_geometry(scheme, wm_geom, zoom))
        # Remove dupes if geoms overlapped.
        tiles = set(tiles)
        # Group by group_zoom_level.
        zip_d = defaultdict(list)
        for t in tiles:
            zip_d[scheme.quadkey(t)[:group_zoom_level]].append(t)
        del tiles
        # Note that at this stage we have all the XYZ tiles per group_zoom_level.
        te = time.time()
        files.set_postfix({'status': f'Tile Grid Generated in {te - ts} seconds'})
        files.set_postfix({'status': 'Downloading Tiles'})
        ts = time.time()
        r_tiles = []
        fid = 0
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
        if len(zip_d) > max_cores:
            num_cores = max_cores
            if max_threads:
                num_threads = max_threads / num_cores
            else:
                num_threads = 5
            files.set_postfix({'status': f'Downloading Tiles using {num_cores} Cores & {num_threads} Threads Per Core'})
        else:
            num_cores = len(zip_d)
            if max_threads:
                num_threads = max_threads / num_cores
            else:
                num_threads = ceil((system_cores * 5) / num_cores)
            files.set_postfix({'status': f'Processing tiles using {num_cores} Cores | Downloading Tiles using {num_threads} Threads Per Core'})

        with concurrent.futures.ProcessPoolExecutor(num_cores) as executor:
            with tqdm(total=len(zip_d)) as progress:
                jobs = []
                for zzl in zip_d:
                    jobs.append(executor.submit(_process_tiles, nearmap, project_folder, tiles_folder, zzl, zip_d,
                                                out_image_format, out_manifest, num_threads, surveyid, tileResourceType,
                                                tertiary, since, until, mosaic, include, exclude, rate_limit_mode))
                # results = []
                for job in jobs:
                    result = job.result()
                    r_tiles.extend(result)
                    progress.update()
        te = time.time()
        files.set_postfix({'status': f'Downloaded and Zipped Tiles in {te - ts} seconds'})
        del zip_d
        if out_manifest:
            ts = time.time()
            files.set_postfix({'status': 'Begin Loading Manifest to GeoDataFrame'})
            # print(f'Begin Loading Manifest to GeoDataFrame')
            result = gpd.GeoDataFrame(r_tiles).set_crs('epsg:4326')
            del r_tiles
            te = time.time()
            files.set_postfix({'status': f'Loaded Manifest as GeoDataFrame in {te - ts} seconds'})
            files.set_postfix({'status': 'Begin Exporting Results to geojson file'})
            ts = time.time()
            manifest_file = project_folder / "manifest.geojson"
            result.to_file(manifest_file, driver='GeoJSON')
            te = time.time()
            files.set_postfix({'status': f"Exported to GeoJSON in {te - ts} seconds"})
            ts = time.time()
            files.set_postfix({'status': 'Begin Exporting Result Extents to geojson file'})
            manifest_extents_file = project_folder / "manifest_extents.geojson"
            result.dissolve(by="zip_zoom").to_file(manifest_extents_file, driver='GeoJSON')
            del result
            te = time.time()
            files.set_postfix({'status': f"Exported to GeoJSON in {te - ts} seconds"})
        rmtree(tiles_folder, ignore_errors=True)
        end = time.time()  # End Clocking
        files.set_postfix({'status': f"Processed in {end - start} seconds"})


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here
    nearmap = NEARMAP(api_key)

    '''
    Data Preparation Instructions:
    
    Input Directory must be a folder with .geojson files formatted as "StateAbbrev_PlaceFIPS_PlaceName_Source.geojson"
    GeoJSON files must also be projected in WGS 1984 'EPSG:4326'
    Example: "FL_1245025_MiamiBeach_Source.geojson"
    '''

    input_dir = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\examples\pipelines\production\source'
    output_dir = r'C:\output_tiles_100'
    zoom = 21
    buffer_distance = 0  # 0.5, 1, 5, 10 .... Distance in meters to offset by
    remove_holes = True
    out_image_format = 'jpg'  # 'zip', 'tif', 'jpg  # Attributes grid with necessary values for zipping using zipper.py
    group_zoom_level = 13
    processing_method = None  # Currently Disabled
    out_manifest = True

    ###############################
    # Survey Specific User Params
    #############################

    surveyid = None  # Optional for calling a spefic survey...
    tileResourceType = 'Vert'  # Currently only 'Vert' and 'North' are supported
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None
    rate_limit_mode = 'slow'

    tile_downloader(nearmap, input_dir, output_dir, out_manifest, zoom, buffer_distance, remove_holes, out_image_format,
                    group_zoom_level, processing_method, surveyid, tileResourceType, tertiary, since, until, mosaic,
                    include, exclude, rate_limit_mode)
