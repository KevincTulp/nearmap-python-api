from nearmap.auth import get_api_key
from nearmap import NEARMAP
from pathlib import Path
try:
    from ujson import dump, dumps
except ModuleNotFoundError:
    from json import dump, dumps


# Connect to the Nearmap API for Python
# nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string
nearmap = NEARMAP(get_api_key())
print(f"My API Key Is: {nearmap.api_key}")

root = str(Path(__file__).parents[2]).replace('\\', '/')  # Get root of project

###################
# User Parameters
#################

point = [151.2144030, -33.8580750]  # Coordinate Pair in Lon/Lat ordering
radius = 1  # Range between 1-100
resources = "DetailDsm"  # Options: "DetailDsm", "TrueOrtho", "Vert" or combination ex: "DetailDsm,TrueOrtho,Vert"

coverage = nearmap.coverageStaticMapV2(point, radius, resources)
print(dumps(coverage, indent=4, sort_keys=True))

surveyID = coverage["surveys"][0]["id"]  # Gets most recent surveyID
image_type = resources
file_format = "tif"  # Member of: "tif", "jpg", "png", "jgw", "pgw", "tfw"
size = "5000x5000"  # Maximum size = "5000x5000"
transactionToken = coverage["transactionToken"]
print(transactionToken)
out_image = f"test_tile.{file_format}"
out_image = f"{root}/nearmap/unit_tests/TestData/scratch/dsm_output.{file_format}"
print(out_image)
get_image = nearmap.imageStaticMapV2(surveyID, image_type, file_format, point, radius, size, transactionToken,
                                     out_image)
