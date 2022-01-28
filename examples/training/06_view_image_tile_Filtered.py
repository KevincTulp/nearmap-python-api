from nearmap import NEARMAP
from PIL import Image, ImageFilter
import os

from PIL.ImageFilter import (
   BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE,
   EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN
)

api_key = os.environ.get("API_KEY")
nearmap = NEARMAP(api_key)

####################
# get tile Inputs
#################

z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"
filter_of_interest = CONTOUR  # Options: [BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN]

# Get Vert Image Tile as Bytes
tileResourceType = "Vert"
vert_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
vert_imBytes = Image.open(vert_image_tile_bytes)
vert_imBytesFiltered = vert_imBytes.filter(filter_of_interest)
#vert_imBytesFiltered.show()

# Get Vert Image Tile as Bytes
tileResourceType = "North"
north_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
north_imBytes = Image.open(north_image_tile_bytes)
north_imBytesFiltered = north_imBytes.filter(filter_of_interest)
#north_imBytesFiltered.show()

# Get Vert Image Tile as Bytes
tileResourceType = "South"
south_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
south_imBytes = Image.open(south_image_tile_bytes)
south_imBytesFiltered = south_imBytes.filter(filter_of_interest)
#south_imBytesFiltered.show()

# Get Vert Image Tile as Bytes
tileResourceType = "East"
east_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
east_imBytes = Image.open(east_image_tile_bytes)
east_imBytesFiltered = east_imBytes.filter(filter_of_interest)
#east_imBytesFiltered.show()

# Get Vert Image Tile as Bytes
tileResourceType = "West"
west_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
west_imBytes = Image.open(west_image_tile_bytes)
west_imBytesFiltered = west_imBytes.filter(filter_of_interest)
#west_imBytesFiltered.show()

merged_image = Image.new('RGB', (5*vert_imBytes.size[0], vert_imBytes.size[1]), (250, 250, 250))
merged_image.paste(vert_imBytesFiltered, (0, 0))
merged_image.paste(north_imBytesFiltered, (vert_imBytes.size[0], 0))
merged_image.paste(south_imBytesFiltered, (vert_imBytes.size[0]*2, 0))
merged_image.paste(east_imBytesFiltered, (vert_imBytes.size[0]*3, 0))
merged_image.paste(west_imBytesFiltered, (vert_imBytes.size[0]*4, 0))
merged_image.show()
