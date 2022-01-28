from nearmap import NEARMAP
from PIL import Image
import os
from nearmap.geospatial.fileio import lat_lon_to_slippy_coords

api_key = os.environ.get("NEARMAP_API_KEY")
nearmap = NEARMAP(api_key)

####################
# get tile Inputs
#################

zoom = 19
lat_deg = 40.76248769686459
lon_deg = -111.89575293016202
format = "jpg"
out_image = f"test_image.{format}"

# Convert lat, lon and zoom to x,y,z
x, y = lat_lon_to_slippy_coords(lat_deg, lon_deg, zoom)
z = zoom

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
