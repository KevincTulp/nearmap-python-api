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

polygon = [-87.73101994900836, 41.79082699478777,
           -87.73056822386012, 41.79083207215124,
           -87.73055971145155, 41.79050035022655,
           -87.73101767903275, 41.79047834820146,
           -87.73101767903275, 41.79047834820146,
           -87.73101994900836, 41.79082699478777]
since = None  # Since Data ex: "2018-08-01"
until = None  # Until Date ex: "2021-07-09"
limit = 20
offset = None
fields = None
sort = None
overlap = None
include = None
exclude = None
lat_lon_direction = "yx"

##########
# Script
########

polygon_coverage = nearmap.polyV2(polygon, since, until, limit, offset, fields, sort, overlap, include, exclude,
                                  lat_lon_direction)
#polygon_coverage = nearmap.polyV2(polygon)

print(dumps(polygon_coverage, indent=4, sort_keys=True))
print(len(polygon_coverage['surveys']))
assert len(polygon_coverage["surveys"]) > 0, "Error: empty json object returned.. No Features Detected"
