from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path
import pandas as pd
from glob import glob
from shutil import rmtree
from os.path import basename, dirname
from os import rename


def batch_download_ortho(api_key, in_spreadsheet, fid_name, lat_name, lon_name, out_folder, distance,
                         image_format="jpg", tertiary=None, since=None, until=None, mosaic=None, include=None,
                         exclude=None, res=None):

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

    df['download_status'] = ""
    for index, row in df.iterrows():
        print(row[fid_name], row[lat_name], row[lon_name])
        try:
            polygon = _point_to_square_polygon(in_coords=[row[lon_name], row[lat_name]], segment_length=distance * 2)
            print(polygon)
            out_file_basename = f"{out_folder}/f_{row[fid_name]}_"
            nearmap.download_ortho(polygon, out_file_basename, image_format, tertiary, since, until, mosaic,
                                   include, exclude, res)
            _restructure_data(out_file_basename, out_folder)
            df.loc[index, ["download_status"]] = "Success"
        except ModuleNotFoundError as e:
            print(e)
            exit()
        except:
            print(f"No Surveys Detected for {row['pol']}'")
            df.loc[index, ["download_status"]] = "Fail"

    df.to_csv(f"{out_folder}\\results.csv")


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Data Processing Specific Parameters

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Paste or type your API Key here as a string

    in_spreadsheet = r''  # r'Input.csv'  # Input spreadsheet for processing in csv or excel(xlsx) format
    fid_name = 'fid'  # The FeatureID unique identifier header name for locations of interest
    lat_name = 'lat'  # Latitude header name
    lon_name = 'lon'  # Longitude header name

    out_folder = r'OrthoImagery'
    image_format = "tif"  # Member of "tif", "jpg", "jp2", "png", "cog"
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None
    distance = 100

    batch_download_ortho(api_key, in_spreadsheet, fid_name, lat_name, lon_name, out_folder, distance,
                         image_format, tertiary, since, until, mosaic, include, exclude)
