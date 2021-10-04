from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path
from shutil import rmtree
from os.path import exists
from glob import glob1

root = str(Path(__file__).parents[2]).replace('\\', '/')  # Get root of project


def ping_server(api_key, region="us"):
    z, x, y = [19, 119799, 215845]
    if region == "anz":
        z, x, y, = [21, 1855981, 1265938]
    url = f'https://api.nearmap.com/tiles/v3/Vert/{z}/{x}/{y}.jpg?apikey={api_key}'
    from requests import get
    return get(url, stream=True)

#################
# JSON TEST DATA
################
# in_feature = f"{root}/unit_tests/TestData/Vector/JSON/FormattedGeoJSON/AOI.json"
# in_feature = f"{root}/unit_tests/examples/TestData/Vector/JSON/Unformatted/AOI.json"
# in_feature = f"{root}/unit_tests/TestData/Vector/JSON/Colt_Gateway.json"
in_feature = f"{root}/unit_tests/TestData/Vector/JSON/Large_AOI.geojson"

################
# KMZ Test Data
###############
# in_feature = f"{root}/unit_tests/TestData/Vector/KMZ/AOI.kmz"
#in_feature = f"{root}/unit_tests/TestData/Vector/KML/doc.kml"

################
# SHP Test Data
###############
# in_feature = f"{root}/unit_tests/TestData/Vector/SHP/AOI.shp"

################
# GDB Test Data
##############
# in_feature = f"{root}/unit_tests/TestData/Vector/GDB/TestData.gdb/AOI"

out_folder = f"{root}/unit_tests/TestData/scratch"
tertiary = None
since = None
until = None
mosaic = None
include = None
exclude = None

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())  # Paste or type your API Key here as a string

num_passes = 100

file_format = "tif"


def delete_folder_if_exists(in_folder):
    if exists(in_folder):
        rmtree(out_folder)


for count, value in enumerate(range(0, num_passes)):
    delete_folder_if_exists(out_folder)
    print(f"\n Processing Pass {count}")
    ping_response = ping_server(nearmap.api_key, "us").headers
    print("start:")
    print(ping_response)
    nearmap.download_ortho(in_feature, out_folder, tertiary, since, until, mosaic, include, exclude)
    num_rasters = len(glob1(out_folder, f"*.{file_format}"))
    print(f"end: Produced {num_rasters} {file_format} Raster Tiles")
    ping_response = ping_server(nearmap.api_key, "us").headers
    print(ping_response)
