from nearmap import NEARMAP
from PIL import Image
import os

api_key = os.environ.get("NEARMAP_API_KEY")
nearmap = NEARMAP(api_key)

####################
# get tile Inputs
#################

z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"

# Get Vert Image Tile as Bytes
tileResourceType = "Vert"
image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
imBytes = Image.open(image_tile_bytes)
imBytes.show()

# Get Vert Image Tile as Bytes
tileResourceType = "North"
image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
imBytes = Image.open(image_tile_bytes)
imBytes.show()

# Get Vert Image Tile as Bytes
tileResourceType = "South"
image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
imBytes = Image.open(image_tile_bytes)
imBytes.show()

# Get Vert Image Tile as Bytes
tileResourceType = "East"
image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
imBytes = Image.open(image_tile_bytes)
imBytes.show()

# Get Vert Image Tile as Bytes
tileResourceType = "West"
image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
imBytes = Image.open(image_tile_bytes)
imBytes.show()
