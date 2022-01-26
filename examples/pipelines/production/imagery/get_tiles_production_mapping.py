from nearmap.auth import get_api_key
from nearmap._api import _get_image
from nearmap import NEARMAP
from pathlib import Path
from math import log, tan, radians, cos, atan, sinh, pi, degrees, floor, ceil
import fiona
from fiona.transform import transform_geom
from shapely.geometry import Polygon, box, shape, mapping
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
import sys
import os
from os import cpu_count
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly

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

    nodata_value = 0
    for f in tile_list:
        x, y, z = f.stem.split("_")
        bounds = tile_edges(int(x), int(y), int(z))
        ext = f.suffix
        f_out = None
        if ext == ".jpg":
            # f_out = (scratch_dir_georeg / f'{f.name}').as_posix()
            #f_out = (scratch_dir_georeg / f'{f.stem}.tif').as_posix()
            f_out = (scratch_dir_georeg / f'{f.stem}.jpg').as_posix()
            #gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds, bandList=[1, 2, 3, "mask"])
            gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds, noData=0, bandList=[1, 2, 3])
        elif ext == ".png":
            #f_out = (scratch_dir_georeg / f'{f.stem}.tif').as_posix()
            f_out = (scratch_dir_georeg / f'{f.stem}.tif').as_posix()
            #gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds)
            gdal.Translate(f_out, f.as_posix(), outputSRS='EPSG:4326', outputBounds=bounds, noData=255, bandList=[1, 2, 3])
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
    #try:
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


def _download_tiles(in_params, out_manifest):
    url = in_params.get('url')
    path = in_params.get('path')
    fid = in_params.get('id')
    ext = Path(path).suffix.replace(".", "")
    # print(url, ext, path)
    image = _get_image(url=url, out_format=ext, out_image=path.as_posix(), rate_limit_mode="slow", quiet=True)
    if image:
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
            m['quadkey'] = in_params.get('quadkey')
            m['success'] = True
            m['file'] = image
            return m
    else:
        return None


def _process_tiles(nearmap, project_folder, tiles_folder, quadkey, zip_d, out_image_format, compression, jpeg_quality,
                   processing_method, out_manifest, num_threads, surveyid, tileResourceType, tertiary, since, until,
                   mosaic, include, exclude, rate_limit_mode, geom=None):

    fid = 0
    jobs = []
    quadkey_tiles_folder = tiles_folder / f'{quadkey}'
    _create_folder(quadkey_tiles_folder)

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
        for t in zip_d.get(quadkey):
            z = t.z
            x = t.x
            y = t.y
            path = quadkey_tiles_folder / f'{t.x}_{t.y}_{t.z}.img'
            url = eval(url_template)
            temp = dict()
            temp['id'] = fid
            temp['url'] = url
            temp['path'] = path
            temp['x'] = t.x
            temp['y'] = t.y
            temp['zoom'] = t.z
            temp['quadkey'] = quadkey
            jobs.append(executor.submit(_download_tiles, temp, out_manifest))
            fid += 1
    results = []
    for job in jobs:
        result = job.result()
        if result is not None:
            results.append(result)
    if any(results):
        if out_image_format.lower() == 'zip':
            zip_dir(quadkey_tiles_folder, project_folder / f'{quadkey}.zip')
            rmtree(quadkey_tiles_folder, ignore_errors=True)
        elif out_image_format is None:
            pass
        else:
            quadkey_scratch_folder = tiles_folder / f'scratch_{quadkey}'
            _create_folder(quadkey_scratch_folder)
            georeference_tiles(quadkey_tiles_folder, project_folder, quadkey_scratch_folder, out_image_format, compression,
                               jpeg_quality, image_basename=quadkey, geom=geom, processing_method=processing_method)
            rmtree(quadkey_tiles_folder, ignore_errors=True)
            rmtree(quadkey_scratch_folder, ignore_errors=True)
        return results
    else:
        return None


def tile_downloader(nearmap, input, output_dir, out_manifest, zoom, buffer_distance, remove_holes, out_image_format,
                    compression=None, jpeg_quality=75, group_zoom_level=13, processing_method=None, surveyid=None,
                    tileResourceType='Vert', tertiary=None, since=None, until=None, mosaic=None, include=None,
                    exclude=None, rate_limit_mode="slow", max_cores=None, max_threads=None):

    input = Path(input).resolve()
    output_dir = Path(output_dir).resolve()

    assert input.is_dir() or input.is_file(), \
        f"Error: 'input_dir' {input} is not a folder/directory or File"
    assert not output_dir.is_file(), f"Error: 'output_dir' {output_dir} cannot be a file... must be a folder/directory"

    supported_formats = ['.geojson']
    files = None
    if input.is_dir():
        files = tqdm([f for f in list(Path(input).iterdir()) if f.suffix in supported_formats])
    elif input.is_file():
        files = tqdm([input])
    else:
        print(f"Error: 'input' File not supported or reading error... |  {input}")
    in_geojson = None
    for file in files:
        geom_mask = None
        if file.suffix == ".geojson":
            in_geojson = file
        files.set_description(f"Processing {file.name}")
        name_string = Path(in_geojson).stem
        proj_folder_str = ""
        for _ in name_string.split("_")[:-1]:
            proj_folder_str = proj_folder_str + f"{_}/"
        proj_folder_str = proj_folder_str + name_string.split("_")[-1]
        project_folder = Path(output_dir / proj_folder_str)
        _create_folder(project_folder)
        tiles_folder = project_folder / 'tiles'
        files.set_postfix({'status': 'Generating Tile Grid'})
        start = time.time()
        ts = time.time()
        geoms = []
        scheme = tiletanic.tileschemes.WebMercator()
        in_geojson = Path(in_geojson)
        with fiona.open(in_geojson) as src:
            src_crs = src.crs.get('init').upper()
            for rec in src:
                if src_crs != 'EPSG:3857':
                    wm_geom = shape(transform_geom('EPSG:4326', 'EPSG:3857', rec.get('geometry')))
                else:
                    wm_geom = shape(rec.get('geometry'))
                if buffer_distance or buffer_distance != 0:
                    wm_geom = wm_geom.buffer(buffer_distance, cap_style=3, join_style=2)
                if remove_holes:
                    wm_geom = Polygon(wm_geom.exterior)
                geoms.append(wm_geom)
        if processing_method in ["mask", "bounds"]:
            geom_mask = ops.unary_union(geoms)
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
                num_threads = 2
            files.set_postfix({'status': f'Downloading Tiles using {num_cores} Cores & {num_threads} Threads Per Core'})
        else:
            num_cores = len(zip_d)
            if max_threads:
                num_threads = max_threads / num_cores
            else:
                num_threads = ceil((system_cores * 2) / num_cores)
            files.set_postfix({'status': f'Processing tiles using {num_cores} Cores | Downloading Tiles using {num_threads} Threads Per Core'})

        with concurrent.futures.ProcessPoolExecutor(num_cores) as executor:
            with tqdm(total=len(zip_d)) as progress:
                    jobs = []
                    for quadkey in zip_d:
                        jobs.append(executor.submit(_process_tiles, nearmap, project_folder, tiles_folder, quadkey, zip_d,
                                                    out_image_format, compression, jpeg_quality, processing_method,
                                                    out_manifest, num_threads, surveyid, tileResourceType, tertiary, since,
                                                    until, mosaic, include, exclude, rate_limit_mode, geom=geom_mask))
                    # results = []
                    for job in jobs:
                        result = job.result()
                        if result is not None:
                            r_tiles.extend(result)
                        progress.update()
        te = time.time()
        if len(r_tiles) > 0:
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
                result.dissolve(by="quadkey").drop(columns="file", axis=1).to_file(manifest_extents_file, driver='GeoJSON')
                del result
                te = time.time()
                files.set_postfix({'status': f"Exported to GeoJSON in {te - ts} seconds"})
            rmtree(tiles_folder, ignore_errors=True)
            end = time.time()  # End Clocking
            files.set_postfix({'status': f"Processed in {end - start} seconds"})
        else:
            print("No Imagery Detected & Downloaded for Area of Interest.. "
                  "Check Nearmap coverage to ensure coverage exists")


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

    input = r'../test_data'  # Input Directory or File (geojson).
                             # Use underscores in filename to designate output directory structure
                             # ex: my_file_name.geojson converts to: output_dir/my/file/name'
    output_dir = r'C:\output_tiles'
    zoom = 21
    buffer_distance = 0  # Options: 0.5, 1, 5, 10, etc... Distance in meters to offset by
    remove_holes = True
    out_image_format = 'tif'  # Options: 'tif', 'jpg' or 'zip'
    compression = 'JPEG'  # Options: [JPEG/LZW/PACKBITS/DEFLATE/CCITTRLE/CCITTFAX3/CCITTFAX4/LZMA/ZSTD/LERC/LERC_DEFLATE/LERC_ZSTD/WEBP/JXL/NONE]
    jpeg_quality = 75  # Only used if using JPEG Compression range[1-100]
    group_zoom_level = 14
    processing_method = "mask"  # Options: "mask" "bounds" or None <-- Enables Masking or clipping of image to input polygon but takes much longer to process
    out_manifest = True  # Output a manifest of data extracted

    ###############################
    # Survey Specific User Params
    #############################

    surveyid = None  # Optional for calling a specific survey...
    tileResourceType = 'Vert'  # Currently only 'Vert' and 'North' are supported
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None
    rate_limit_mode = 'slow'

    tile_downloader(nearmap, input, output_dir, out_manifest, zoom, buffer_distance, remove_holes, out_image_format,
                    compression, jpeg_quality, group_zoom_level, processing_method, surveyid, tileResourceType, tertiary, since,
                    until, mosaic, include, exclude, rate_limit_mode)
