from nearmap import NEARMAP
from nearmap.auth import get_api_key
try:
    from ujson import dump, dumps
except ModuleNotFoundError:
    from json import dump, dumps

# Connect to the Nearmap API for Python
# nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string

nearmap = NEARMAP(get_api_key())
# print(f"My API Key Is: {nearmap.api_key}")


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
packs = None  # ex: "building" # Set to None for all packs otherwise type pack of interest name(s)

##########
# Script
########


'''
# query available ai packs
my_packs = nearmap.aiPacksV4()
print(dumps(my_packs, indent=4, sort_keys=True))

# query available ai classes
my_classes = nearmap.aiClassesV4()
print(dumps(my_classes, indent=4, sort_keys=True))

# Get AI Features as Pandas Dataframe
df = nearmap.aiFeaturesV4(polygon, since=None, until=None, packs=None, out_format="pandas", lat_lon_direction="yx")
print(df)
'''

'''
# Get AI Features as JSON
my_ai_features = nearmap.aiFeaturesV4(polygon, since, until, packs, out_format="json", lat_lon_direction="yx")
print(dumps(my_ai_features, indent=4, sort_keys=True))
print(my_ai_features)

# Save AI features to JSON File
with open('my_data.json', 'w', encoding='utf-8') as f:
    dump(my_ai_features, f, ensure_ascii=False, indent=4)
'''


# Get AI Features as geojson
out_format = "geojson"
output = r'test_folder'
my_ai_features = nearmap.aiFeaturesV4(polygon, since, until, packs, out_format, output, lat_lon_direction="yx")


'''
# Get AI Features as geopackage
out_format = "gpkg"
output = "test_file.gpkg"
my_ai_features = nearmap.aiFeaturesV4(polygon, since, until, packs, out_format, output, lat_lon_direction="yx")
'''

'''
# Get AI Features as shapefile
out_format = "shp"
output = r"test_file"
my_ai_features = nearmap.aiFeaturesV4(polygon, since, until, packs, out_format, output, lat_lon_direction="yx")
'''

'''
# Get AI Features as geopandas
out_format = "geopandas"
my_ai_features = nearmap.aiFeaturesV4(polygon, since, until, packs, out_format, output, lat_lon_direction="yx")
'''