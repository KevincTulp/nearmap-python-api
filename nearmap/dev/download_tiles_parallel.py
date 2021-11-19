import os
import time
from tqdm import tqdm
from nearmap.auth import get_api_key
from nearmap._api import _get_image
from pathlib import Path
from shutil import rmtree
import geopandas as gpd
import concurrent.futures
from pathlib import Path


def download_tiles(in_params):
    url = in_params.get('url')
    path = in_params.get('path')
    ext = Path(path).suffix.replace(".","")
    #print(url, ext, path)
    _get_image(url=url, out_format=ext, out_image=path, rate_limit_mode="slow")


def threaded_get_tiles(api_key, in_geojson, output_dir, threads=25):

    def _create_folder(folder):
        folder = Path(folder)
        if folder.exists():
            rmtree(folder)
        folder.mkdir(parents=True, exist_ok=False)
        return folder

    assert Path(in_geojson).suffix.lower() in '.geojson', f'error: in_geojson not detected as geojson file: {in_geojson}'

    scratch_folder = output_dir

    Path(scratch_folder).mkdir(parents=True, exist_ok=True)
    tiles_folder = f'{scratch_folder}\\tiles'
    zip_folder = f'{scratch_folder}\\zips'
    [_create_folder(f) for f in [scratch_folder, tiles_folder, zip_folder]]
    urls = []

    start = time.time()
    itr = 0
    gdf = gpd.read_file(in_geojson)
    print(f"Preparing to download {len(gdf.index)} tiles")

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(threads) as executor:
        for index, row in tqdm(gdf.iterrows(), total=gdf.shape[0]):
            url = f'https://api.nearmap.com/tiles/v3/Vert/{row["zoom"]}/{row["x"]}/{row["y"]}.img?apikey={api_key}'
            path = f'{tiles_folder}\\{row["x"]}_{row["y"]}_{row["zoom"]}.img'
            temp = dict()
            temp['url'] = url
            temp['path'] = path
            temp['x'] = row["x"]
            temp['y'] = row["y"]
            temp['zoom'] = row["zoom"]
            urls.append(temp)
            itr += 1
            jobs.append(executor.submit(download_tiles, temp))
    print(f"Begin Downloading Tiles")

    results = []
    for job in jobs:
        result = job.result()
        # print(result)

    end = time.time()
    print(f"Downloaded Image Tiles complete in {end - start} Seconds")

if __name__ == "__main__":

    ###############
    # User Inputs
    #############

    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here

    threads = 25
    output_dir = os.path.join(os.path.abspath(''), 'miami_beach_data')
    in_geojson = r'miami_beachOOO_1.geojson'

    threaded_get_tiles(api_key, in_geojson, output_dir, threads)