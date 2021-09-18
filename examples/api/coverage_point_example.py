from nearmap import NEARMAP
from nearmap.auth import get_api_key
try:
    from ujson import dump, dumps
except ModuleNotFoundError:
    from json import dump, dumps

# Connect to the Nearmap API for Python
# nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string
nearmap = NEARMAP(get_api_key())
print(f"My API Key Is: {nearmap.api_key}")

###################
# User Parameters
#################

point = [-87.73101994900836, 41.79082699478777]
since = None  # Since Data ex: "2018-08-01"
until = None  # Until Date ex: "2021-07-09"
limit = 20
offset = None
fields = None
sort = None
include = None
exclude = None
lat_lon_direction = "yx"

##########
# Script
########

point_coverage = nearmap.pointV2(point, since, until, limit, offset, fields, sort, include, exclude, lat_lon_direction)
print(dumps(point_coverage, indent=4, sort_keys=True))

