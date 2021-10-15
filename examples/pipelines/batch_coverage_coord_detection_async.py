####################################
#   File name: batch_coverage_coord_detection_async.py
#   About: Process for batch detecting whether coordinate pairs fall within nearmap coverage
#   Authors: Geoff Taylor | Sr Solution Architect | Nearmap
#   Date created: 10/15/2021
#   Last update: 10/15/2021
#   Python Version: 3.6+
####################################

import pandas as pd
from pathlib import Path
from nearmap.auth import get_api_key
from math import floor
from psutil import cpu_count
import asyncio
import aiohttp
from shutil import rmtree, move
from tempfile import NamedTemporaryFile
import csv
import time
import os

try:
    from ujson import json
except:
    import json


async def fetch(session, url):
    """ Operation for fetching the json response """
    async with session.get(url) as response:
        return await response.json()


async def worker(name, in_csv, fid_name, lat_name, lon_name, skip_duplicates):
    """ Worker node for the nearmap lat/lon lookup operation """

    # Connect to the Nearmap API for Python
    api_key = get_api_key()

    tempfile = NamedTemporaryFile(mode='w', delete=False)
    fields = ['ID', fid_name, lat_name, lon_name, 'lat_lon_duplicates', 'fid_duplicates', 'nearmap_coverage']
    num_rows = sum(1 for row in open(in_csv))
    intervals = list(range(0, num_rows, 1000))
    count = 0
    with open(in_csv, 'r') as csvfile, tempfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        writer = csv.DictWriter(tempfile, fieldnames=fields, lineterminator='\n')
        for row in reader:
            if row[fid_name]:
                if "False" in [row['lat_lon_duplicates'], row['fid_duplicates']] or not skip_duplicates:
                    try:
                        url = f"https://api.nearmap.com/coverage/v2/point/{row[lon_name]},{row[lat_name]}?apikey={api_key}"
                        async with aiohttp.ClientSession() as session:
                            my_json = await asyncio.gather(fetch(session, url))
                            surveys = my_json[0]['surveys']
                            if surveys:
                                row['nearmap_coverage'] = "True"
                            else:
                                row['nearmap_coverage'] = "False"
                    except:
                        row['nearmap_coverage'] = "Error"
                row = {fields[0]: row[fields[0]], fields[1]: row[fields[1]], fields[2]: row[fields[2]],
                       fields[3]: row[fields[3]], fields[4]: row[fields[4]], fields[5]: row[fields[5]],
                       fields[6]: row[fields[6]]}
                writer.writerow(row)
                '''
                if count in intervals:
                    print(name, f"{round((count / num_rows), 2)}% Complete")
                count += 1
                '''
    move(tempfile.name, in_csv)
    # Notify the queue that the "work item" has been processed.
    print(f"Complete Processing File: {name}")
    return in_csv


async def process_coords(csv_files, fid_name, lat_name, lon_name, skip_duplicates):
    """ Asynchronous process for processing whether or not lat/lon coords are within Nearmap Coverage"""
    tasks = []
    for count, df in enumerate(csv_files):
        tasks.append(worker(f"process_{count}", df, fid_name, lat_name, lon_name, skip_duplicates))
    await asyncio.gather(*tasks)
    return csv_files


def check_duplicates(in_spreadsheet, fid_name, lat_name, lon_name):
    """ Process for detecting duplicates in spreadsheet & returning as pandas dataframe """

    file_extension = Path(in_spreadsheet).suffix.lower()
    supported_formats = [".csv", ".xlsx"]
    assert file_extension in supported_formats, f"Error: file format {file_extension} not supported... " \
                                                f"Supported Formats: {supported_formats}"
    if file_extension == ".csv":
        df = pd.read_csv(in_spreadsheet, usecols=[fid_name, lat_name, lon_name], skip_blank_lines=True)
    else:
        df = pd.read_excel(in_spreadsheet, usecols=[fid_name, lat_name, lon_name], skip_blank_lines=True)

    lat_lon_duplicates = df.duplicated(subset=[lat_name, lon_name]).rename("lat_lon_duplicates")
    try:
        assert True not in lat_lon_duplicates, \
            f"Error: Input file contains Lat/Lon Duplicates for: {lat_name, lon_name} fields."
    except AssertionError as e:
        print(e)
    df = df.merge(lat_lon_duplicates.to_frame(), left_index=True, right_index=True)
    del lat_lon_duplicates
    fid_name_duplicates = df.duplicated(subset=[lat_name, lon_name]).rename("fid_duplicates")
    try:
        assert True not in fid_name_duplicates, \
            f"Error: Input file contains Duplicates for FID Name : '{fid_name}' field."
    except AssertionError as e:
        print(e)
    if True in fid_name_duplicates:
        print(f"Detected duplicates for FID Name : {fid_name}")
    df = df.merge(fid_name_duplicates.to_frame(), left_index=True, right_index=True)
    del fid_name_duplicates
    return df


def main(in_spreadsheet, fid_name, lat_name, lon_name, out_spreadsheet, skip_duplicates=True):
    """ Operation to batch detect whether a given lat/lon falls within Nearmap Coverage """

    def _file_exists(in_spreadsheet):
        path = Path(in_spreadsheet)
        assert path.is_file(), f"Error: input file does not exist: {in_spreadsheet}"

    _file_exists(in_spreadsheet)
    file_extension = Path(out_spreadsheet).suffix.lower()
    supported_extensions = [".csv", ".xlsx"]
    assert file_extension in supported_extensions, f"Error, output spreadsheet extension not supported. " \
                                                   f"Must be of {supported_extensions}"

    # Load spreadsheet to dataframe, and check for duplicates
    df = check_duplicates(in_spreadsheet, fid_name, lat_name, lon_name)
    # Add boolean coverage field
    df["nearmap_coverage"] = ""

    num_splits = cpu_count()
    num_features = df.shape[0]
    if num_features < num_splits:
        num_splits = 1
    split_list = list(range(0, num_features, floor(num_features/num_splits)))[:-1] + [num_features]
    splits = [(split_list[i], split_list[i+1]) for i, _ in enumerate(split_list[:-1])]
    dataframes = [df.iloc[i[0]:i[1]] for i in splits]
    scratch_folder = r'scratch_folder'
    p = Path(scratch_folder)
    if p.exists():
        rmtree(p)
    p.mkdir(parents=True, exist_ok=False)
    csv_files = []
    for count, dataframe in enumerate(dataframes):
        csv_file = f"{scratch_folder}/file_{count}.csv"
        dataframe.to_csv(csv_file)
        csv_files.append(csv_file)

    # Pass csv_files into asyncio process
    if os.name == 'nt':  # If Windows add event loop policy to resolve asyncio bug
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_coords(csv_files, fid_name, lat_name, lon_name, skip_duplicates))
    loop.close()

    df = pd.concat(map(pd.read_csv, csv_files), ignore_index=True)

    # Save Dataframe to Spreadsheet
    file_extension = Path(out_spreadsheet).suffix.lower()
    if file_extension == ".csv":
        df.to_csv(out_spreadsheet)
    elif file_extension == ".xlsx":
        df.to_excel(out_spreadsheet)
    del df
    return out_spreadsheet


if __name__ == "__main__":

    # User Inputs
    in_spreadsheet = r''
    fid_name = 'fid'
    lat_name = 'lat'
    lon_name = 'lon'
    out_spreadsheet = r''
    skip_duplicates = True

    # Run Script
    start_time = time.time()
    main(in_spreadsheet, fid_name, lat_name, lon_name, out_spreadsheet, skip_duplicates)
    print(f"Total Processing Time: {time.time() - start_time}")
