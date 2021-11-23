from nearmap.dev.slippy_tile_gen import slippy_tile_gen
from nearmap.dev.download_tiles_parallel import threaded_get_tiles
from nearmap.dev.zipper_3 import threaded_zip_files
from nearmap.auth import get_api_key
from pathlib import Path
from shutil import rmtree
import time


def _create_folder(folder):
    folder = Path(folder)
    # if folder.exists():
    #    rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def batch_process(in_folder, output_folder, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level, overwrite_images, threads):
    files = list(Path(in_folder).iterdir())
    for f in files:
        if f.suffix == ".geojson":
            in_geojson = f
            # in_geojson naming structure must follow 'StateAbbrev_PlaceCode_CityName_Source.geojson'

        start_time = time.time()
        print(f"begin processing {f}")

        name_string = Path(in_geojson).stem.replace("_Source", "")
        state_abbrev = name_string.split("_")[0]
        place_name = f'{name_string.split("_")[1]}_{name_string.split("_")[2]}'
        output_dir = f'{output_folder}/{state_abbrev}/{place_name}'
        _create_folder(output_dir)

        ''''''
        print(f"begin generating tile processing manifest for {f}")
        slippy_geojson = Path(f"{output_dir}/{place_name}.geojson").resolve()
        slippy_tile_gen(in_geojson, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level, place_name)


        print(f"begin downloading tiles for {f}")
        # Set Directory where tiles will be stored
        threaded_get_tiles(api_key, slippy_geojson, output_dir, overwrite_images, threads)

        tiles_dir = Path(f"{output_dir}/tiles").resolve()
        threaded_zip_files(tiles_dir, slippy_geojson, threads)
        # Delete Scratch Tile folder to free up space
        rmtree(tiles_dir, ignore_errors=True)

        # TODO: DevOps! Implement the following
        print(f"begin transferring data to S3 {f}")
        # Implement Folder to Boto3 Trasfer Here!!!!!!!!!!!
        ### pipe the entire directory 'output_dir' to the clients s3 bucket
            # Example: 4.	https://gist.github.com/feelinc/d1f541af4f31d09a2ec3

        # Delete Date from machine to free up space
        rmtree(Path(f'{output_folder}/{state_abbrev}').resolve(), ignore_errors=True, onerror=None)

        end_time = time.time()
        print(f"Complete Processing {f} in {end_time - start_time} Seconds")


if __name__ == "__main__":

    ###############
    # User Inputs
    #############

    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here

    in_folder = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\nearmap\dev\source' # Input folder containing the Source GeoJSON Files for Processing
    output_folder = r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\nearmap\dev\processing'
    zoom = 21 # Imagery Tile Zoom Level for Downloading
    buffer_distance = None  # Currently Not Working
    remove_holes = True  # Option to remove holes from input geometries
    zip_tiles = True  # Attributes grid with necessary values for zipping using zipper.py
    zip_zoom_level = 13  # Level based on slippy tile zoom levels group data for zipping

    overwrite_images = False # Best to keep set to False ;)
    threads = 25  # Set Number of Threads for concurrent processing based on Hardware being used.

    batch_process(in_folder, output_folder, zoom, buffer_distance, remove_holes, zip_tiles, zip_zoom_level,
                  overwrite_images, threads)
