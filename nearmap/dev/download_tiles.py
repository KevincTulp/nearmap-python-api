import aiohttp
import asyncio
import aiofiles
import os
import time
from math import log, tan, radians, cos, atan, sinh, pi, degrees
from nearmap.auth import get_api_key
from pathlib import Path
from shutil import rmtree
from osgeo.gdal import Translate
try:
    from osgeo_utils import gdal_merge
except ImportError:
    from osgeo.utils import gdal_merge


def sec(x):
    return 1/cos(x)


def latlon_to_xy(lat, lon, z):
    tile_count = pow(2, z)
    xtile = (lon + 180) / 360
    ytile = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return int(tile_count*xtile), int(tile_count*ytile)


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


async def get(session, url, path):
    try:
        async with session.get(url=url) as response:
            if response.status != 200:
                print('Response Code:', response.status)
            # TODO: check header for image format and return .png vs jpg
            async for data in response.content.iter_chunked(1024):
                async with aiofiles.open(path, "ba") as f:
                    await f.write(data)
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e.__class__))


async def get_tiles_client(urls, max_threads):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=max_threads)) as session:
        return await asyncio.gather(*[asyncio.create_task(get(session, url['url'], url['path'])) for url in urls])


def get_tiles(api_key, zoom, start_x, start_y, x_tiles, y_tiles, output_dir, max_threads=25, method="merge",
              out_format="tif"):

    def _create_folder(folder):
        folder = Path(folder)
        if folder.exists():
            rmtree(folder)
        folder.mkdir(parents=True, exist_ok=False)
        return folder

    method = method.lower()
    available_methods = ["merge", "georeference", "tile", None]
    assert method in available_methods, f"Method: {method} not in {available_methods}"
    available_formats = ['tif', None]
    assert out_format in available_formats, f'Out_Format: {out_format} not in {available_formats}'

    scratch_folder = os.path.join(os.path.abspath(''), 'scratch_folder')
    unprocessed_folder = f'{scratch_folder}\\unprocessed'
    georeferenced_folder = f'{scratch_folder}\\georeferenced'
    [_create_folder(f) for f in [scratch_folder, unprocessed_folder, georeferenced_folder]]

    urls = []
    start = time.time()
    itr = 0
    for y in range(start_y, start_y + y_tiles):
        for x in range(start_x, start_x + x_tiles):
            url = f'https://api.nearmap.com/tiles/v3/Vert/{zoom}/{x}/{y}.img?apikey={api_key}'
            path = f'{unprocessed_folder}\\{x}_{y}_{zoom}.jpg'
            temp = dict()
            temp['url'] = url
            temp['path'] = path
            temp['x'] = x
            temp['y'] = y
            temp['zoom'] = zoom
            urls.append(temp)
            itr += 1
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_tiles_client(urls, max_threads))
    end = time.time()
    print(f"Downloaded Image Tiles in {end - start} Seconds")
    if method in ["merge", "georeference", None]:
        start = time.time()

        def _georeference_tile(in_file, out_file, x, y, zoom):
            bounds = tile_edges(x, y, zoom)
            # filename, extension = os.path.splitext(path)
            Translate(out_file, in_file, outputSRS='EPSG:4326', outputBounds=bounds)

        georeferenced_tiles = []
        # TODO: Implement multiprocessing pool for gdal translate operation
        for url in urls:
            in_image = url.get('path')
            out_image = f'{georeferenced_folder}\\{Path(in_image).name}'
            _georeference_tile(in_image, out_image, url.get('x'), url.get('y'), url.get('zoom'))
            georeferenced_tiles.append(out_image)
        rmtree(unprocessed_folder)
        end = time.time()
        print(f"Georeferenced Image Tiles in {end - start} Seconds")
        if method in [None, "merge"]:
            start = time.time()
            _create_folder(output_dir)

            def _merge_tiles(in_rasters, out_raster, out_format):
                # Only options - GTiff (the default) or HFA (Erdas Imagine)
                parameters = ['', '-o', out_raster, '-of', out_format] + in_rasters
                gdal_merge.main(parameters)
                return out_raster

            formats = {'tif': {'gdal_name': 'GTiff'},
                       'jpg': {'gdal_name': 'JPG'},
                       'png': {'gdal_name': 'PNG'}
                       }

            out_raster = f'{output_dir}\\image_0.{out_format}'
            raster = _merge_tiles(georeferenced_tiles, out_raster, formats.get('tif').get('gdal_name'))
            end = time.time()
            print(f"Merged Image Tiles in {end - start} Seconds")
            #rmtree(scratch_folder)
            return raster


if __name__ == "__main__":

    ###############
    # User Inputs
    #############

    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here

    '''
    start_x = 1928740
    start_y = 1257469
    '''
    lat = -87.73101994900836
    lon = 41.79082699478777
    zoom = 21
    max_threads = 25
    x_tiles = 100
    y_tiles = 100
    output_dir = os.path.join(os.path.abspath(''), 'output')
    method = "merge"  # Options: "merge", "georeference", "tile", "retile"
    out_format = "tif"

    # Run Script
    start_x, start_y = latlon_to_xy(lon, lat, zoom)
    get_tiles(api_key, zoom, start_x, start_y, x_tiles, y_tiles, output_dir, max_threads, method, out_format)
