from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path

root = str(Path(__file__).parents[2]).replace('\\', '/')  # Get root of project

#################
# JSON TEST DATA
################
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/JSON/FormattedGeoJSON/AOI.json"
# in_feature = f"{root}/nearmap/unit_tests/examples/TestData/Vector/JSON/Unformatted/AOI.json"
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/JSON/Colt_Gateway.json"

################
# KMZ Test Data
###############
in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/KMZ/boston_sub_aoi.kmz"
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/KML/doc.kml"

################
# SHP Test Data
###############
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/SHP/AOI.shp"

################
# GDB Test Data
##############
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/GDB/TestData.gdb/AOI"

out_folder = f"{root}/nearmap/unit_tests/TestData/scratch"
tertiary = None
since = None
until = None
mosaic = None
include = None
exclude = None
packs = None
out_format = "json"  # Of Type: "json" or "gpkg"

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())  # Paste or type your API Key here as a string

nearmap.download_multi(in_feature, out_folder, tertiary, since, until, mosaic, include, exclude, packs, out_format)
