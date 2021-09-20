from nearmap import NEARMAP
from nearmap.auth import get_api_key
from PIL import Image


# Connect to the Nearmap API for Python
# nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string
nearmap = NEARMAP(get_api_key())
print(f"My API Key Is: {nearmap.api_key}")

####################
# get tile Inputs
#################

tileResourceType = "Vert"
z = 20
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"

# Get Image Tile as Bytes
image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes")
imBytes = Image.open(image_tile_bytes)
imBytes.show()

tileResourceType = "South"
# Get Image Tile as File
image_tile_file = nearmap.tileV3(tileResourceType, z, x, y, format, out_image)
imFile = Image.open(image_tile_file)
imFile.show()
