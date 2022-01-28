from nearmap import NEARMAP
from nearmap.geospatial.fileio import lat_lon_to_slippy_coords
from PIL import Image, ImageDraw
import os

from PIL.ImageFilter import (
   BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE,
   EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN
)

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
image_pixel_offset = 25
filter_of_interest = CONTOUR # Options: [BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN]

# Convert lat, lon and zoom to x,y,z
x, y = lat_lon_to_slippy_coords(lat_deg, lon_deg, zoom)
z = zoom

# Get Vert Image Tile as Bytes
tileResourceType = "Vert"
vert_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
vert_imBytes = Image.open(vert_image_tile_bytes)
vert_imBytesFiltered = vert_imBytes.filter(filter_of_interest)

# Get Vert Image Tile as Bytes
tileResourceType = "North"
north_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
north_imBytes = Image.open(north_image_tile_bytes)
north_imBytesFiltered = north_imBytes.filter(filter_of_interest)

# Get Vert Image Tile as Bytes
tileResourceType = "South"
south_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
south_imBytes = Image.open(south_image_tile_bytes)
south_imBytesFiltered = south_imBytes.filter(filter_of_interest)

# Get Vert Image Tile as Bytes
tileResourceType = "East"
east_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
east_imBytes = Image.open(east_image_tile_bytes)
east_imBytesFiltered = east_imBytes.filter(filter_of_interest)

# Get Vert Image Tile as Bytes
tileResourceType = "West"
west_image_tile_bytes = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes", rate_limit_mode="slow")
west_imBytes = Image.open(west_image_tile_bytes)
west_imBytesFiltered = west_imBytes.filter(filter_of_interest)

# Merge the Tiles into a single image
img_list = [["Vert", vert_imBytesFiltered], ["North", north_imBytesFiltered], ["South", south_imBytesFiltered],
            ["East", east_imBytesFiltered], ["West", west_imBytesFiltered]]
len = sum([_[1].size[0] for _ in img_list]) + (image_pixel_offset*len(img_list))
height = max([_[1].size[1] for _ in img_list]) + (image_pixel_offset*2)
merged_image = Image.new('RGB', (len, height), (250, 250, 250))
total_x_offset = 0
for i, val in enumerate(img_list):
    image = val[1]
    if i == 0:
        offset_x = image_pixel_offset
    else:
        offset_x = image.size[0] + image_pixel_offset
    total_x_offset += offset_x
    offset_y = image_pixel_offset
    merged_image.paste(image, (total_x_offset, offset_y))
img_draw = ImageDraw.Draw(merged_image)
total_x_offset = 0
for i, val in enumerate(img_list):
    image = val[1]
    text = val[0]
    if i == 0:
        offset_x = image_pixel_offset
    else:
        offset_x = image.size[0] + image_pixel_offset
    total_x_offset += offset_x
    img_draw.text((total_x_offset, image_pixel_offset/2), text, fill='black')
merged_image.show()
merged_image.save(out_image)
