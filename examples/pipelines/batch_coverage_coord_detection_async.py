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
from nearmap import NEARMAP

try:
    from ujson import json
except:
    import json


async def fetch(session, url):
    """ Operation for fetching the json response """
    async with session.get(url) as response:
        return await response.json()


async def worker(name, url, api_key, in_csv, fid_name, lat_name, lon_name, skip_duplicates, since, until, limit, offset,
                         fields, sort, include, exclude):
    """ Worker node for the nearmap lat/lon lookup operation """

    tempfile = NamedTemporaryFile(mode='w', delete=False)
    csv_fields = ['ID', fid_name, lat_name, lon_name, 'lat_lon_duplicates', 'fid_duplicates', 'nearmap_coverage']
    num_rows = sum(1 for row in open(in_csv))
    # intervals = list(range(0, num_rows, 1000))
    # count = 0
    with open(in_csv, 'r') as csvfile, tempfile:
        reader = csv.DictReader(csvfile, fieldnames=csv_fields)
        writer = csv.DictWriter(tempfile, fieldnames=csv_fields, lineterminator='\n')
        for row in reader:
            if row[fid_name]:
                if "False" in [row['lat_lon_duplicates'], row['fid_duplicates']] or not skip_duplicates:
                    try:
                        point = f"{row[lon_name]},{row[lat_name]}"
                        # url = f"https://api.nearmap.com/coverage/v2/point/{row[lon_name]},{row[lat_name]}?apikey={api_key}"
                        async with aiohttp.ClientSession() as session:
                            my_json = await asyncio.gather(fetch(session, eval(url)))
                            surveys = my_json[0]['surveys']
                            if surveys:
                                row['nearmap_coverage'] = "True"
                            else:
                                row['nearmap_coverage'] = "False"
                    except:
                        row['nearmap_coverage'] = "Error"
                row = {csv_fields[0]: row[csv_fields[0]], csv_fields[1]: row[csv_fields[1]],
                       csv_fields[2]: row[csv_fields[2]], csv_fields[3]: row[csv_fields[3]],
                       csv_fields[4]: row[csv_fields[4]], csv_fields[5]: row[csv_fields[5]],
                       csv_fields[6]: row[csv_fields[6]]}
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


async def process_coords(api_key, csv_files, fid_name, lat_name, lon_name, skip_duplicates, since, until, limit, offset,
                         fields, sort, include, exclude):
    """ Asynchronous process for processing whether or not lat/lon coords are within Nearmap Coverage"""
    # Connect to the Nearmap API for Python
    nearmap = NEARMAP(api_key)
    url = nearmap.pointV2([0, 0], since, until, limit, offset, fields, sort, include, exclude, output="url")
    tasks = []
    for count, file in enumerate(csv_files):
        tasks.append(worker(f"process_{count}", url, api_key, file, fid_name, lat_name, lon_name, skip_duplicates, since,
                            until, limit, offset, fields, sort, include, exclude))
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


def main(api_key, in_spreadsheet, fid_name, lat_name, lon_name, out_spreadsheet, skip_duplicates, since, until,
         limit, offset, fields, sort, include, exclude):
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
    loop.run_until_complete(process_coords(api_key, csv_files, fid_name, lat_name, lon_name, skip_duplicates, since,
                                           until, limit, offset, fields, sort, include, exclude))
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

    ###############
    # User Inputs
    #############

    # Data Processing Specific Parameters
    in_spreadsheet = r''  # Input spreadsheet for processing in csv or excel(xlsx) format
    fid_name = 'fid'  # The FeatureID unique identifier header name for locations of interest
    lat_name = 'lat'  # Latitude header name
    lon_name = 'lon'  # Longitude header name
    out_spreadsheet = r''  # Output spreadsheet in .csv or excel(xlsx) format

    # Nearmap API Specific Parameters
    api_key = get_api_key()  # Edit api key in nearmap/api_key.py -or- type api key as string here
    skip_duplicates = True
    since = None  # Since Data ex: "2018-08-01"
    until = None  # Until Date ex: "2021-07-09"
    limit = 20
    offset = None
    fields = None
    sort = None
    include = None
    exclude = None

    # Run Script
    start_time = time.time()
    main(api_key, in_spreadsheet, fid_name, lat_name, lon_name, out_spreadsheet, skip_duplicates, since, until, limit,
         offset, fields, sort, include, exclude)
    print(f"Total Processing Time: {time.time() - start_time}")
