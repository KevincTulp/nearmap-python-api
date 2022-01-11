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
fileFormat = "geojson"
since = None  # Since Data ex: "2018-08-01"
until = None  # Until Date ex: "2021-07-09"
limit = 20
offset = None
resources = None
overlap = None
include = None
exclude = None
lat_lon_direction = "yx"

##########
# Script
########

survey_coverage = nearmap.surveyV2(polygon, fileFormat, since, until, limit, offset, resources, overlap, include,
                                   exclude, lat_lon_direction)
print(dumps(survey_coverage, indent=4, sort_keys=True))

# Save AI features to JSON File
with open('survey_coverage.geojson', 'w', encoding='utf-8') as f:
    dump(survey_coverage, f, ensure_ascii=False, indent=4)
