from nearmap.geospatial.fileio import lat_lon_to_slippy_coords
from nearmap import NEARMAP
import os
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
from PIL import Image

from PIL.ImageFilter import (
   BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE,
   EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN
)

api_key = os.environ.get("NEARMAP_API_KEY")
nearmap = NEARMAP(api_key)

zoom = 19
lat_deg = 40.76248769686459
lon_deg = -111.89575293016202
tileResourceType = "West"
format = "img"
num_rows = 4
num_cols = 4
axis_padding = 0.0
enable_axis = False
filter_of_interest = EMBOSS  # Options: [None, BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN]
out_file = r'test.jpg'

# Convert lat, lon and zoom to x,y,z
x, y = lat_lon_to_slippy_coords(lat_deg, lon_deg, zoom)

figure = plt.figure(figsize=(12., 12.))
tile_grid = ImageGrid(figure,
                      111,
                      nrows_ncols=(num_rows, num_cols),
                      axes_pad=axis_padding)

grid_coords = [[row, col] for col in range(num_cols) for row in range(num_rows)]

rotations = {"Vert": 0, "North": 0, "South": 180, "East": 270, "West": 90}

for axis, (tile_x, tile_y) in zip(tile_grid, grid_coords):
    image = Image.open(
        nearmap.tileV3(tileResourceType, zoom, x+tile_x, y+tile_y, format,
                       "bytes", rate_limit_mode="slow"))
    if filter_of_interest:
        image = image.filter(filter_of_interest)
    axis.imshow(image.rotate(rotations.get(tileResourceType)))
    if enable_axis:
        axis.axis('on')
    else:
        axis.axis('off')
plt.savefig(out_file, bbox_inches='tight', pad_inches=0)
plt.show()
