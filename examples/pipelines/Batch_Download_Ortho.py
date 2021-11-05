from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path
import pandas as pd
from glob import glob
from shutil import rmtree
from os.path import basename, dirname
from os import rename
import concurrent.futures


def threaded_batch_download_ortho(api_key, in_spreadsheet, fid_name, lat_name, lon_name, out_folder, distance,
                                  image_format="jpg", tertiary=None, since=None, until=None, mosaic=None, include=None,
                                  exclude=None, res=None, threads=4):

    def _batch_download_ortho(fid_name, fid, longitude, latitude, distance):
        try:
            polygon = _point_to_square_polygon(in_coords=[longitude, latitude], segment_length=distance * 2)
            out_file_basename = f"{out_folder}/{fid}_"
            nearmap.download_ortho(polygon, out_file_basename, image_format, tertiary, since, until, mosaic,
                                   include, exclude, res)
            _restructure_data(out_file_basename, out_folder)
            return {fid_name: fid, 'result': 'Success'}
        except Exception as e:
            return {fid_name: fid, 'result': 'Fail', 'error': e}

    def _point_to_square_polygon(in_coords, segment_length):
        length = segment_length
        xmin = in_coords[0] - 0.00000000001
        xmax = in_coords[0] + 0.00000000001
        ymin = in_coords[1] - 0.00000000001
        ymax = in_coords[1] + 0.00000000001
        return [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]

    def _restructure_data(in_folder, out_folder):
        files = glob(f'{in_folder}/*')
        for file in files:
            unique_id = basename(dirname(file)).replace('f_', '')
            file_name = basename(file)
            new_file = f'{out_folder}/{file_name.replace("ortho_", "ortho_" + unique_id)}'
            rename(file, new_file)
        rmtree(in_folder)

    def _file_exists(in_spreadsheet):
        path = Path(in_spreadsheet)
        assert path.is_file(), f"Error: input file does not exist: {in_spreadsheet}"

    _file_exists(in_spreadsheet)
    file_extension = Path(in_spreadsheet).suffix.lower()
    supported_extensions = [".csv", ".xlsx"]
    assert file_extension in supported_extensions, f"Error, output spreadsheet extension not supported. " \
                                                   f"Must be of {supported_extensions}"
    if file_extension == ".csv":
        df = pd.read_csv(in_spreadsheet, usecols=[fid_name, lat_name, lon_name], skip_blank_lines=True)
    else:
        df = pd.read_excel(in_spreadsheet, usecols=[fid_name, lat_name, lon_name], skip_blank_lines=True)

    nearmap = NEARMAP(api_key)

    p = Path(out_folder)
    if p.exists():
        rmtree(p)
    p.mkdir(parents=True, exist_ok=False)

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(threads) as executor:
        for index, row in df.iterrows():
            jobs.append(executor.submit(_batch_download_ortho, fid_name, row[fid_name], row[lon_name], row[lat_name],
                                        distance))
    results = []
    for job in jobs:
        results.append(job.result())
    print(results)
    df = pd.DataFrame(results, columns=[fid_name, 'result'])
    df.to_csv(f"{out_folder}\\results.csv")
    return


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Data Processing Specific Parameters

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Paste or type your API Key here as a string

    in_spreadsheet = r'test_data.csv'  # r'Input.csv'  # Input spreadsheet for processing in csv or excel(xlsx) format
    fid_name = 'pol'  # The FeatureID unique identifier header name for locations of interest
    lat_name = 'lat'  # Latitude header name
    lon_name = 'long'  # Longitude header name

    out_folder = r'OrthoImagery'
    image_format = "tif"  # Member of "tif", "jpg", "jp2", "png", "cog"
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None
    distance = 100

    # System Parameters

    threaded_batch_download_ortho(api_key, in_spreadsheet, fid_name, lat_name, lon_name, out_folder, distance,
                                  image_format, tertiary, since, until, mosaic, include, exclude, threads=10)
