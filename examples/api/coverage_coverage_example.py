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

# Additional User Parameters are optional

##########
# Script
########

coverage = nearmap.coverageV2() # ["features"]
print(dumps(coverage, indent=4, sort_keys=True))


# Save AI features to JSON File
with open('coverage_data.geojson', 'w', encoding='utf-8') as f:
    dump(coverage, f, ensure_ascii=False, indent=4)
