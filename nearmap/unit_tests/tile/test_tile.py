from nearmap import NEARMAP
from nearmap.auth import get_api_key
from os.path import isfile
from os import remove

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key())

####################
# get tile Inputs
#################

tileResourceType = "Vert"
z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"
# TODO: Implement unit tests for optional input parameters.


def test_tile_bytes():
    image_tile = nearmap.tileV3(tileResourceType, z, x, y, format, "bytes")
    assert image_tile.getbuffer().nbytes > 0, "Error: No Byte Stream Detected"


def test_tile_file():
    image_tile = nearmap.tileV3(tileResourceType, z, x, y, format, out_image)
    assert isfile(image_tile), f"Error: File not detected {image_tile}"
    remove(image_tile)
