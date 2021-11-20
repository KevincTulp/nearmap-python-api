import geopandas as gpd
from pathlib import Path
import concurrent.futures
import time
from zipfile import ZipFile
import pandas as pd
import os


def list_files(in_folder):
    """ Obtain a dictionary of files"""
    files = list(Path(in_folder).iterdir())
    d = dict()
    id = 0
    for f in files:
        nd = dict()
        nd["file"] = f
        nd["expected_tile_name"] = f.stem
        d[id] = nd
        id += 1
    return pd.DataFrame.from_dict(d, orient='index', columns=['file', 'expected_tile_name'])


def zip_files(in_data_list):
    os.chdir(processing_folder)
    # TODO: Add output zipfile name
    with ZipFile(in_data_list[1] + ".zip", 'w') as zipF:
        for index, row in in_data_list[0].iterrows():
            if type(row['file']) == float: #TODO this is temp, probably better way to classify and scip when a file isnt found.
                pass
            else:
                zipF.write(os.path.basename(os.path.normpath(row['file'])))

    #             # TODO placeholder for testing
    #         # TODO replace below with the appropriate dataframe header
    #         # TODO: If necessary change the working directory using os.chdir(root_directory_of_source_files)... this should be added before the with statement in this function
    #


def threaded_zip_files(processing_folder, manifest_gdf, threads: int = 10):

    start = time.time()  # Begin Clocking Initial Data Prep
    large_grids = []
    for row, column in manifest_gdf.iterrows():
        large_grids.append(str(column.zip_x) + '_' + str(column.zip_y) + '_' + '13')
    manifest_gdf['large_grids'] = large_grids  # add column to pandas dataframe of all tiles
    large_grids = list(manifest_gdf['large_grids'].unique())  # get unique values for z13 grids

    list_of_tile_names = []  # for current large grid
    for row, column in manifest_gdf.iterrows():
        list_of_tile_names.append(str(column.x) + '_' + str(column.y) + '_' + str(column.zoom))
    manifest_gdf['expected_tile_name'] = list_of_tile_names

    my_files_df = list_files(processing_folder)
    merged_df = pd.merge(manifest_gdf, my_files_df, how='left', on='expected_tile_name')

    df_list = []
    for grid in list(merged_df['large_grids'].unique()):
        df_list.append([merged_df[merged_df["large_grids"] == grid],grid])
    # df_list = [[df0, "grid_name"], [df1, "grid_name"]]
    # print(merged_df['expected_tile_name'].unique())

    end = time.time()  # End Clocking Initial Data Prep
    print(f"Inital Data Processing Calculations Complete in {end - start} Seconds")

    start = time.time()  # Begin Clocking Threadded Zipping Operation

    if len(df_list) < threads:
        threads = len(df_list)

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(threads) as executor:
        # TODO uncomment out the code below and remove the single dataframe processing version
        for df in df_list:
            jobs.append(executor.submit(zip_files, df))
        '''
        for df in [df_list[0]]:
            jobs.append(executor.submit(zip_files, df))
        '''
    print(f"Begin Zipping Tiles")

    results = []
    for job in jobs:
        result = job.result()

    end = time.time()  # End Clocking Clocking Threadded Zipping Operation
    print(f"Zipping Image Tiles Complete in {end - start} Seconds")
    print(f"The number of images in the manifest for this section was: {len(df_list[0][0])}")

    print("Exporting out Manifest")
    # TODO Join Pandas Dataframe to Geopandas source dataset as a new geopandas dataframe
    # TODO: Save Geopandas Dataframe as geojson in the project folder <-- Becomes the manifest


if __name__ == "__main__":

    ###############
    # User Inputs
    #############

    root = str(Path(__file__).parents[2]).replace('\\', '/')  # Get root of project
    # processing_folder = f"{root}/nearmap/unit_tests/TestData/snap"
    processing_folder = r"C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\nearmap\dev\miami_beach_data\tiles"
    manifest_gdf = gpd.read_file(r'C:\Users\geoff.taylor\PycharmProjects\nearmap-python-api\nearmap\dev\miami_beachOOO_1.geojson')
    threads = 25

    # Begin Script
    threaded_zip_files(processing_folder, manifest_gdf, threads)
