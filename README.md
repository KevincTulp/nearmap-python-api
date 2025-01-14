# nearmap
Nearmap API for Python: Beta 0.1.0 release.

Initial Instructions:

1.) Install **One** of the following versions:
- ["Standard Dependencies Libraries + Nearmap-Python-API"](./install/README.md) 

or 
- ["Standard + Advanced Analytics Libraries + Nearmap-Python-API"](./install/advanced_analytics/README.md) 

Please refer to the installation instructions above. DO NOT install via PIP.
- <i>As the Nearmap-Python-API is currently in BETA it is installed in Development Mode. We will be releasing 
"Conda-Forge" and "PIP Install" deployments in the future. The following installation methodology ensures 
compatibility across operating systems and cpu architectures.</i>

2.) Access example implementation scripts for all API operations in the ["examples folder"](./examples)
- Note: For Production Mapping please refer to the "Pipelines/Production" and "Downloads" Examples.

_** The Library is constantly being updated**_

Example Usage for API Calls:

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
- since="2015-10-31"
- until="2020-10-31"
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
