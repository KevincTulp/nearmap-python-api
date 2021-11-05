from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path
import pandas as pd
import geopandas as gpd
from glob import glob
from shutil import rmtree
from os.path import basename, dirname
from os import rename
import concurrent.futures


def batch_download_ortho(api_key, in_geojson, fid_name, unique_id_name, geometry_name, out_folder, image_format="jpg",
                         tertiary=None, since=None, until=None, mosaic=None, include=None,
                         exclude=None, res=None, threads=10):

    def _batch_download_ortho(fid_name, fid, unique_id_name, unique_id, polygon):
        try:
            out_file_basename = f"{out_folder}/{fid}_{unique_id}_"
            nearmap.download_ortho(polygon, out_file_basename, image_format, tertiary, since, until, mosaic,
                                   include, exclude, res)
            _restructure_data(out_file_basename, out_folder)
            return {fid_name: fid, unique_id_name: unique_id, 'result': 'Success'}
        except:
            return {fid_name: fid, unique_id_name: unique_id, 'result': 'Fail'}

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

    _file_exists(in_geojson)
    file_extension = Path(in_geojson).suffix.lower()
    supported_extensions = [".geojson"]
    assert file_extension in supported_extensions, f"Error, input file extension not supported. " \
                                                   f"Must be of {supported_extensions}"

    gdf = gpd.read_file(in_geojson)


    nearmap = NEARMAP(api_key)

    p = Path(out_folder)
    if p.exists():
        rmtree(p)
    p.mkdir(parents=True, exist_ok=False)

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(threads) as executor:
        for index, row in gdf.iterrows():
            polygon = list(row.get(geometry_name).exterior.coords)
            jobs.append(executor.submit(_batch_download_ortho, fid_name, row[fid_name], unique_id_name,
                                        row[unique_id_name], polygon))
    results = []
    for job in jobs:
        results.append(job.result())
    print(results)
    df = pd.DataFrame(results, columns=[fid_name, unique_id_name, 'result'])
    df.to_csv(f"{out_folder}\\results.csv")
    return


if __name__ == "__main__":
    ###############
    # User Inputs
    #############

    # Data Processing Specific Parameters

    # Connect to the Nearmap API for Python
    api_key = get_api_key()  # Paste or type your API Key here as a string

    in_geojson = r'path_togeojson_file.geojson'  # Input Polygon GeoJson File

    fid_name = 'My_Unique_Id_For_All_Features'  # Unique Feature ID for all geometries. Numbers can't exist > 1x in the dataset
    unique_id_name = 'My_Unique_Parcel_ID'  # Parcel Lookup Code
    geometry_name = 'geometry'  # Name for the geometry in geopandas

    out_folder = r'output_folder_for_storing_imagery'
    image_format = "jpg"  # Member of "tif", "jpg", "jp2", "png", "cog"
    tertiary = None
    since = None
    until = None
    mosaic = None
    include = None
    exclude = None

    batch_download_ortho(api_key, in_geojson, fid_name, unique_id_name, geometry_name, out_folder, image_format,
                         tertiary, since, until, mosaic, include, exclude, threads=4)
