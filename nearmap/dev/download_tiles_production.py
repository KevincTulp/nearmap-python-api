import aiohttp
import asyncio
import aiofiles
import os
import time
from tqdm import tqdm
from nearmap.auth import get_api_key
from pathlib import Path
from shutil import rmtree
import geopandas as gpd

def _http_response_error_reporting(status):
    if status == 200:
        return '200 OK: Success'
    elif status == 400:
        return '400 Bad Request: Returned when the request is invalid. This means either the format is wrong or a ' \
               'value is out of range.'
    elif status == 401:
        return '401 Unauthorized: Returned when the API key is invalid.'
    elif status == 403:
        return '403 Forbidden: Returned when not allowed to access the requested location.'
    elif status == 403:
        return '403 Forbidden: Returned when not allowed to access the requested location.'
    elif status == 404:
        return '404 Not Found: Returned when cannot find any surveys for the requested condition.'
    elif status == 429:
        return '429 Too Many Requests: The rate limit has been reached...'
    elif status == 500:
        return f'{status} Internal Server Error: Unexpected condition was encountered and no more specific message is suitable'
    elif status == 501:
        return f'{status} Not Implemented: Server either does not recognize the request method, or it lacks the ability to fulfill the request.'
    elif status == 502:
        return f'{status} Bad Gateway: Server was acting as a gateway or proxy and received an invalid response from the upstream server'
    elif status == 503:
        return f'{status} Service Unavailable: The server cannot handle the request (because it is overloaded or down for maintenance).'
    elif status == 504:
        return f'{status} Gateway Timeout: Server was acting as a gateway or proxy and did not receive a timely response from the upstream server'
    elif str(status)[:1] == "5":
        return f"{status} Server Error. Returned when something is wrong in the server side."
    else:
        return f"{status} Unknown Error..."


async def download_multi_attempts(session, url, path, sleep_time, attempt, success):
    try:
        print("Get: Are we there yet")
        # await asyncio.sleep(sleep_time)
        time.sleep(sleep_time)
        # await time.sleep(sleep_time)
        print("Get: We are there! it's not the print statement")
        await download_tile(session, url, path, attempt)
        print(f"Get: Success after attempt {attempt} & sleep time {sleep_time}")
        success = True
        return session, url, path, sleep, attempt, success
    except Exception as e:
        print(f"Get: unknown {e} {e.__class__}")
        attempt += 1
        success = False
        return session, url, path, sleep, attempt, success


async def download_tile(session, url, path, attempt=1):
    e = None
    success = False
    async with session.get(url=url) as response:
        if response.status == 404:
            # TODO: Log tile as not existing on server
            print(_http_response_error_reporting(response.status))

        elif response.status == 429 or str(response.status)[:1] == "5":
            ''' Handle 429 and 500 level Errors'''
            e = response.status
            success == False
        elif response.status != 200:
            print(path)
            print('Response Code:', response.status)
            e = response.status
            success == False
        else:
            image_format = response.headers.get('Content-Type').replace('image/', '')
            rate_limit_remaining = int(response.headers.get('x-ratelimit-remaining'))
            # print(path)
            if rate_limit_remaining < 1000:
                print(f"Rate Limit Remaining: {rate_limit_remaining} | Rate Limit Reset: {response.headers.get('x-ratelimit-reset')}")
            base_path = path.replace('.img', '')
            if image_format == "jpeg":
                path = f'{base_path}.jpg'
            elif image_format != "jpeg":
                # print(f'image_format is not jpeg| its {image_format}')
                path = f'{base_path}.png'
            # TODO: check header for image format and return .png vs jpg
            async for data in response.content.iter_chunked(1024):
                async with aiofiles.open(path, "ba") as f:
                    await f.write(data)
                    success = True
    if success == False:
        sleep_time = 0.1
        if attempt >= 3:
            sleep_time = (attempt - 2) * 0.3
            if sleep_time > 1800:
                sleep_time = 0.3
                print("Get Error: Backoff Rate Limit time reached 30 minutes... "
                      "restarting multiples of 0.3 seconds.")
        print(attempt, sleep_time)
        #print(f"Get Error: {attempt} with sleep time {sleep_time} Unable to get url {url} due to {e} {e.__class__}")
        session, url, path, sleep_time, attempt, success = await download_multi_attempts(session, url, path, sleep_time,
                                                                                         attempt, success)


async def get_multi_attempts(session, url, path, sleep_time, attempt, success):
    try:
        print("Get: Are we there yet")
        # await asyncio.sleep(sleep_time)
        time.sleep(sleep_time)
        # await time.sleep(sleep_time)
        print("Get: We are there! it's not the print statement")
        await download_tile(session, url, path, attempt)
        print(f"Get: Success after attempt {attempt} & sleep time {sleep_time}")
        success = True
        return session, url, path, sleep, attempt, success
    except (asyncio.exceptions.TimeoutError, TimeoutError) as e:
        print(f"Get: unknown {e} {e.__class__}")
        attempt += 1
        success = False
        return session, url, path, sleep, attempt, success
    except Exception as e:
        print(f"Get: unknown {e} {e.__class__}")
        attempt += 1
        success = False
        return session, url, path, sleep, attempt, success


async def get(session, url, path, attempt=1):
    success = False
    e = None

    try:
        await download_tile(session, url, path, attempt)
        success = True

    except (asyncio.exceptions.TimeoutError, TimeoutError, PermissionError) as e:
        success = False
        e = e
        attempt += 1

    except Exception as e:
        e = e
        if str(e.__class__) == "<class 'asyncio.exceptions.TimeoutError'>":
            print("d: Unable to get url {} due to {}.".format(url, e.__class__))
        elif str(e) == 'Response Code: 429':
            print("e: Unable to get url {} due to {}.".format(url, e.__class__))
        else:
            print("f: Unable to get url {} due to {}.".format(url, e.__class__))

    while success == False:
        sleep_time = 0.1
        if attempt >= 3:
            sleep_time = (attempt - 2) * 0.3
            if sleep_time > 1800:
                sleep_time = 0.3
                print("Get Error: Backoff Rate Limit time reached 30 minutes... "
                      "restarting multiples of 0.3 seconds.")
        print(f"Get Error: {attempt} with sleep time {sleep_time} Unable to get url {url} due to {e} {e.__class__}")
        print(attempt, sleep_time)
        session, url, path, sleep_time, attempt, success = await get_multi_attempts(session, url, path, sleep_time,
                                                                                    attempt, success)


async def get_tiles_client(urls, max_threads):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=max_threads)) as session:
        # TODO: Implement TQDM here for progress bar
        return await asyncio.gather(*[asyncio.create_task(get(session, url['url'], url['path'])) for url in urls])


def get_tiles(api_key, in_geojson, output_dir, max_threads=25):

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
    print(f"Begin Downloading Tiles")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_tiles_client(urls, max_threads))
    end = time.time()
    print(f"Downloaded Image Tiles complete in {end - start} Seconds")


if __name__ == "__main__":

    ###############
    # User Inputs
    #############

    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here

    max_threads = 25
    output_dir = os.path.join(os.path.abspath(''), 'miami_beach_data')
    in_geojson = r'miami_beachOOO_1.geojson'

    get_tiles(api_key, in_geojson, output_dir, max_threads)
