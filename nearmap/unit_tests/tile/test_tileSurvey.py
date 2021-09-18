from nearmap import NEARMAP
from nearmap.auth import get_api_key
from os.path import isfile
from os import remove
import pytest

# Connect to the Nearmap API for Python
nearmap = NEARMAP(get_api_key)

##########################
# get tileSurvey Inputs
#######################

# tileSurvey Inputs
surveyid = "88f1c072-0bdd-11ea-b266-130e886a3ec4"
contentType = "Vert"
z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"


def test_tile_bytes():
    image_tile = nearmap.tileSurveyV3(surveyid, contentType, z, x, y, format, "bytes")
    assert image_tile.getbuffer().nbytes > 0, "Error: No Byte Stream Detected"


def test_tile_file():
    image_tile = nearmap.tileSurveyV3(surveyid, contentType, z, x, y, format, out_image)
    assert isfile(image_tile), f"Error: File not detected {image_tile}"
    remove(image_tile)
