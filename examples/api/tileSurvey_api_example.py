from nearmap import NEARMAP
from PIL import Image

# Connect to the Nearmap API for Python
# nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string
nearmap = NEARMAP(get_api_key())
print(f"My API Key Is: {nearmap.api_key}")

##########################
# get tileSurvey Inputs
#######################

surveyid = "88f1c072-0bdd-11ea-b266-130e886a3ec4"
contentType = "Vert"
z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"

# Get Image Tile as Bytes
image_tile_bytes = nearmap.tileSurveyV3(surveyid, contentType, z, x, y, format, "bytes")
im0 = Image.open(image_tile_bytes)
im0.show()

# Get Image Tiles as File
image_tile_file = nearmap.tileSurveyV3(surveyid, contentType, z, x, y, format, out_image)
im1 = Image.open(image_tile_file)
im1.show()
