from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path

root = str(Path(__file__).parents[2]).replace('\\', '/')  # Get root of project

#################
# JSON TEST DATA
################
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/JSON/FormattedGeoJSON/AOI.json"
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/JSON/UnformattedGeoJSON/AOI.json"
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/JSON/Colt_Gateway.json"

################
# KMZ Test Data
###############
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/KMZ/AOI.kmz"
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/KML/doc.kml"

################
# SHP Test Data
###############
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/SHP/AOI.shp"

################
# GDB Test Data
##############
in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/GDB/TestData.gdb/AOI"

out_folder = f"{root}/nearmap/unit_tests/TestData/scratch"
since = None  # Since Data ex: "2018-08-01"
until = None   # Until Date ex: "2021-07-09"
packs = None  # Set to None for all packs otherwise type pack of interest name(s)
out_format = "json"  # Of Type: "json" or "gpkg"

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())  # Paste or type your API Key here as a string

all_ai_df = nearmap.download_ai(in_feature, out_folder, since, until, packs, out_format)

# #create some dataframes from the output.
parcel_df = all_ai_df[0]
all_ai_df = all_ai_df[1]
