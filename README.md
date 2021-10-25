# nearmap
Nearmap API for Python: Beta 0.1.0 release.

Initial Instructions:

1.) Install the ["Standard Dependencies"](./install/README.md) or ["Standard + Advanced Analytics Libraries"](./install/advanced_analytics/README.md) using conda

2.) Implement code in your script or jupyter notebook.. Ensure scripts and notebooks are placed within the nearmap-api-python directory.

3.) Access example implementation scripts for all API operations in the ["examples folder"](./examples)

_** The current release of the Nearmap API for Python mainly supports synchronous API calls/operations. 
Asynchronous API calls and more advanced data download operations are continuously being added**_

Example Usage:

Connect to the Nearmap API for Python
```python
from nearmap import NEARMAP
from PIL import Image

api_key = "my_api_key"
nearmap = NEARMAP(api_key)
```

Input parameters for specific Map tiles
```python
tileResourceType = "Vert"
z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"
```
Additional values can alse be input such as:
- tertiary="satellite"
- since=2015-10-31 
- until=2020-10-31
- mosaic="latest"
- include="disaster:hurricane"

Stream map tiles as bytes and view with PIL (Python Imaging Library)
```python
get_tile = nearmap.tile(tileResourceType, z, x, y, format, "bytes")

img = Image.open(get_tile)
img.show()
```

Download map tiles as file and view with PIL (Python Imaging Library)
```python
get_tile = nearmap.tile(tileResourceType, z, x, y, format, out_image)

img = Image.open(get_tile)
img.show()
```

Input parameters for a specific Map TileSurvey
```python
# user inputs
surveyid = "88f1c072-0bdd-11ea-b266-130e886a3ec4"
contentType = "Vert"
z = 19
x = 119799
y = 215845
format = "jpg"
out_image = f"test_image.{format}"
```

Stream map tileSurvey as bytes and view with PIL (Python Imaging Library)
```python
get_tile = nearmap.tileSurvey(surveyid, contentType, z, x, y, format, "bytes")

img = Image.open(get_tile)
img.show()
```

Download map tileSurvey as file and view with PIL (Python Imaging Library)
```python
get_tile = nearmap.tileSurvey(surveyid, contentType, z, x, y, format, out_image)

img = Image.open(get_tile)
img.show()
```

Contact: geoff.taylor@nearmap.com with any questions/bugs/issues.
