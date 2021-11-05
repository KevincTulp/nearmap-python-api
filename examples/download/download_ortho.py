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
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/KMZ/AOI.kmz"

################
# SHP Test Data
###############
in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/SHP/AOI.shp"

################
# GDB Test Data
##############
# in_feature = f"{root}/nearmap/unit_tests/TestData/Vector/GDB/TestData.gdb/AOI"

out_folder = f"{root}/nearmap/unit_tests/TestData/scratch"
out_format = "tif"  # Member of "tif", "jpg", "jp2", "png", "cog"
tertiary = None
since = None
until = None
mosaic = None
include = None
exclude = None

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())  # Paste or type your API Key here as a string

nearmap.download_ortho(in_feature, out_folder, out_format, tertiary, since, until, mosaic, include, exclude)
