from nearmap.auth import get_api_key
from nearmap._api import _get_image
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
import os

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


def zip_files(in_file_list, processing_folder, out_file_name):
    os.chdir(processing_folder)
    # TODO: Add output zipfile name
    with ZipFile(f"../../{out_file_name}", 'w') as zipF:
        for i in in_file_list:
            f = Path(i.get('file'))
            if f.is_file():
                zipF.write(f.name)
    os.chdir(Path(processing_folder).parents[0])


def zip_dir(source, destination):
    base = Path(destination)
    name = base.stem
    file_format = base.suffix.strip(".")
    archive_from = Path(source).parents[0]
    archive_to = Path(source).name
    print(source, destination, archive_from, archive_to)
    make_archive(name, file_format, archive_from, archive_to)
    #move(base.name, base.parents)


def _download_tiles(in_params, out_manifest):
    url = in_params.get('url')
    path = in_params.get('path')
    fid = in_params.get('id')
    ext = Path(path).suffix.replace(".","")
    #print(url, ext, path)
    image = _get_image(url=url, out_format=ext, out_image=path, rate_limit_mode="slow")
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


def _process_tiles(api_key, project_folder, tiles_folder, zzl, zip_d, out_manifest, num_threads):
    fid = 0
    jobs = []
    scratch_folder = f'{tiles_folder}/{zzl}'
    _create_folder(scratch_folder)
    with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
        for t in zip_d.get(zzl):
            url = f'https://api.nearmap.com/tiles/v3/Vert/{t.z}/{t.x}/{t.y}.img?apikey={api_key}'
            path = f'{scratch_folder}\\{t.x}_{t.y}_{t.z}.img'
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
    zip_dir(scratch_folder, f'{project_folder}\\{zzl}.zip')
    # zip_files(in_file_list=results, processing_folder=scratch_folder, out_file_name=f"{zzl}.zip")
    #rmtree(scratch_folder)
    return results


def tile_downloader(api_key, input_dir, output_dir, out_manifest, zoom, buffer_distance, remove_holes, zip_tiles,
                    zip_zoom_level, threads):

    files = tqdm(list(Path(input_dir).iterdir()))
    in_geojson = None
    for file in files:
        if file.suffix == ".geojson":
            in_geojson = file
        files.set_description(f"Processing {file.name}")
        name_string = Path(in_geojson).stem.replace("_Source", "")
        state_abbrev = name_string.split("_")[0]
        place_name = f'{name_string.split("_")[1]}_{name_string.split("_")[2]}'
        project_folder = f'{output_dir}/{state_abbrev}/{place_name}'
        _create_folder(project_folder)
        tiles_folder = f'{project_folder}/tiles'
        files.set_postfix({'status': 'Generating Tile Grid'})
        start = time.time()
        ts = time.time()
        geoms = []
        scheme = tiletanic.tileschemes.WebMercator()
        in_geojson = Path(in_geojson)
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
        del tiles
        # Note that at this stage we have all the XYZ tiles per zip_zoom_level.
        te = time.time()
        files.set_postfix({'status': f'Tile Grid Generated in {te - ts} seconds'});
        files.set_postfix({'status': 'Downloading Tiles'})
        ts = time.time()
        r_tiles = []
        fid = 0
        time.sleep(0.1)  # Sleep Temporarily to ensure previous stats are printed

        num_threads = None
        sub_threads = None
        print(f'Threads: {threads} | zip_d: {len(zip_d)}')
        if len(zip_d) > threads:
            num_threads = floor(threads/2)
            sub_threads = 2
            print(f"MainThreads: {num_threads} | SubThreads {sub_threads}")
        else:
            num_threads = len(zip_d)
            sub_threads = ceil(threads/len(zip_d))
            print(f"MainThreads: {num_threads} | SubThreads {sub_threads}")
        #exit()

        with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
            jobs = []
            for zzl in zip_d:
                jobs.append(executor.submit(_process_tiles, api_key, project_folder, tiles_folder, zzl, zip_d,
                                            out_manifest, sub_threads))
            #results = []
            for job in jobs:
                result = job.result()
                #results.append(result)
                r_tiles.extend(result)

        te = time.time()
        files.set_postfix({'status' : f'Downloaded and Zipped Tiles in {te - ts} seconds'});
        del zip_d
        if out_manifest:
            ts = time.time()
            files.set_postfix({'status': 'Begin Loading Manifest to GeoDataFrame'})
            #print(f'Begin Loading Manifest to GeoDataFrame')
            result = gpd.GeoDataFrame(r_tiles).set_crs('epsg:4326')
            te = time.time()
            files.set_postfix({'status': f'Loaded Manifest as GeoDataFrame in {te - ts} seconds'})
            files.set_postfix({'status': 'Begin Exporting Results to geojson file'})
            ts = time.time()
            result.to_file(f"{project_folder}\\manifest.geojson", driver='GeoJSON')
            te = time.time()
            files.set_postfix({'status': f"Exported to GeoJSON in {te - ts} seconds"})
        end = time.time()  # End Clocking
        files.set_postfix({'status': f"Processed in {end - start} seconds"})


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here

    # Input Directory must be a folder with .geojson files formattes as "StateAbbrev_PlaceFIPS_PlaceName_Source.geojson"
    # Example: "FL_1245025_MiamiBeach_Source.geojson"
    input_dir = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\examples\pipelines\production\source'
    output_dir = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\examples\pipelines\production\output'
    zoom = 21
    buffer_distance = None # Currently Not Working
    remove_holes = True
    zip_tiles = True # Attributes grid with necessary values for zipping using zipper.py
    zip_zoom_level = 13
    out_manifest= True
    threads = 100

    tile_downloader(api_key, input_dir, output_dir, out_manifest, zoom, buffer_distance, remove_holes, zip_tiles,
                    zip_zoom_level, threads)
