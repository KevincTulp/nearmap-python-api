####################################
#   File name: __init__.py
#   About: The Nearmap API for Python
#   Authors: Geoff Taylor | Sr Solution Architect | Nearmap
#            Connor Tluck | Solutions Engineer | Nearmap
#   Date created: 7/7/2021
#   Last update: 9/17/2021
#   Python Version: 3.6+
####################################

from requests import get
from io import BytesIO


try:
    from ujson import loads
except ModuleNotFoundError:
    from json import loads


def format_polygon(polygon, lat_lon_direction):
    if type(polygon) is str:
        polygon = [float(i) for i in polygon.split(",")]
    assert (len(polygon) % 2) == 0, "Error: input geometry does not contain an even number of lat/lon coords"
    if lat_lon_direction.lower() == "xy":
        polygon = polygon.reverse()
    return str(polygon)[1:-1].replace(" ", "")


def download_file(url, out_file):
    # out_file = url.split('/')[-1]
    #out_file is the file path to save to
    #url is the requested data
    r = get(url, stream="true")
    if r.status_code == 200:
        with open(out_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return out_file
    else:
        print(http_response_error_reporting(r.status_code))


def http_response_error_reporting(status):
    if status == 200:
        return '200 OK: Success'
    elif status == 400:
        return '400 Bad Request: Returned when the request is invalid. This means either the format is wrong or a ' \
               'value is out of range.'
    elif status == 401:
        return '401 Unauthorized: Returned when the API key is invalid.'
    elif status == 403:
        return '403 Forbidden: Returned when not allowed to access the requested location.'
    elif status == 403:
        return '403 Forbidden: Returned when not allowed to access the requested location.'
    elif status == 404:
        return '404 Not Found: Returned when cannot find any surveys for the requested condition.'
    elif status == 429:
        return '429 Too Many Requests: The rate limit has been reached... more info ' + \
               'https://docs.nearmap.com/display/ND/New+Standard+for+Nearmap+APIs#NewStandardforNearmapAPIs-RateLimiting'
    elif str(status)[:1] == "5":
        return f"{status} Server Error. Returned when something is wrong in the server side."
    else:
        return f"{status} Unknown Error..."


####################
# Download Features
###################

    # Coming Soon! In Development

###############
#  NEARMAP AI
#############


def aiFeaturesV4(base_url, api_key, polygon, since=None, until=None, packs=None, out_format="json",
                 lat_lon_direction="yx", surveyResourceID=None):
    polygon = format_polygon(polygon, lat_lon_direction)
    # TODO: determine how to implement surveyResourceID parameter
    url = f"{base_url}ai/features/v4/features.json?polygon={polygon.replace(' ','')}"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if packs:
        url += f"&packs={packs}"
    url += f"&apikey={api_key}"
    if out_format == "json":
        return get(url).json()
    elif out_format in ["pandas", "pd"]:
        import pandas as pd
        return pd.read_json(url)["features"]
    else:
        print(f"Error: output out_format {out_format} is not supported.")
        exit()


def aiClassesV4(base_url, api_key, out_format="json"):
    url = f"{base_url}ai/features/v4/classes.json?apikey={api_key}"
    if out_format.lower() in ["pandas", "pd"]:
        import pandas as pd
        return pd.read_json(url)
    elif out_format.lower() == "text":
        return get(url).text
    elif out_format.lower() == "json":
        return get(url).json()
    else:
        print(f"Error: output format {out_format} not a viable option")
        exit()


def aiPacksV4(base_url, api_key, out_format="json"):
    url = f"{base_url}ai/features/v4/packs.json?apikey={api_key}"
    if out_format.lower() in ["pandas", "pd"]:
        import pandas as pd
        return pd.read_json(url)
    elif out_format.lower() == "text":
        return get(url).text
    elif out_format.lower() == "json":
        return get(url).json()
    else:
        print(f"Error: output format {out_format} not a viable option")
        exit()

#####################
#  NEARMAP Coverage
###################


def polyV2(base_url, api_key, polygon, since=None, until=None, limit=20, offset=None, fields=None, sort=None,
           overlap=None, include=None, exclude=None, lat_lon_direction="yx"):
    polygon = format_polygon(polygon, lat_lon_direction)
    url = f"{base_url}coverage/v2/poly/{polygon}"
    url += f"?apikey={api_key}"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if limit:
        url += f"&limit={limit}"
    if offset:
        url += f"&offset={offset}"
    if fields:
        url += f"&fields={fields}"
    if sort:
        url += f"&sort={sort}"
    if overlap:
        url += f"&overlap={overlap}"
    if include:
        url += f"&include={include}"
    if exclude:
        url += f"&exclude={exclude}"
    return get(url).json()


def pointV2(base_url, api_key, point, since=None, until=None, limit=20, offset=None, fields=None, sort=None,
            include=None, exclude=None, lat_lon_direction="yx"):
    point = format_polygon(point, lat_lon_direction)
    url = f"{base_url}coverage/v2/point/{point}"
    url += f"?apikey={api_key}"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if limit:
        url += f"&limit={limit}"
    if offset:
        url += f"&offset={offset}"
    if fields:
        url += f"&fields={fields}"
    if sort:
        url += f"&sort={sort}"
    if include:
        url += f"&include={include}"
    if exclude:
        url += f"&exclude={exclude}"
    return get(url).json()


def coordV2(base_url, api_key, z, x, y, since=None, until=None, limit=20, offset=None, fields=None, sort=None,
            include=None, exclude=None):
    url = f"{base_url}coverage/v2/coord/{z}/{x}/{y}"
    url += f"?apikey={api_key}"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if limit:
        url += f"&limit={limit}"
    if offset:
        url += f"&offset={offset}"
    if fields:
        url += f"&fields={fields}"
    if sort:
        url += f"&sort={sort}"
    if include:
        url += f"&include={include}"
    if exclude:
        url += f"&exclude={exclude}"
    return get(url).json()


def surveyV2(base_url, api_key, polygon, fileFormat="geojson", since=None, until=None, limit=20, offset=None,
             resources=None, overlap=None, include=None, exclude=None, lat_lon_direction="yx"):
    polygon = format_polygon(polygon, lat_lon_direction)
    url = f"{base_url}coverage/v2/surveyresources/boundaries.{fileFormat}"
    url += f"?polygon={polygon}&apikey={api_key}"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if limit:
        url += f"&limit={limit}"
    if offset:
        url += f"&offset={offset}"
    if resources:
        url += f"&resources={resources}"
    if overlap:
        url += f"&overlap={overlap}"
    if include:
        url += f"&include={include}"
    if exclude:
        url += f"&exclude={exclude}"
    return get(url).json()


def coverageV2(base_url, api_key, fileFormat="geojson", types=None):
    url = f"{base_url}coverage/v2/aggregate/boundaries.{fileFormat}?apikey={api_key}"
    if types:
        url += f"&types={types}"
    return get(url).json()


###############################
# NEARMAP DSM & TrueOrtho API
#############################


def coverageStaticMapV2(base_url, api_key, point, radius, resources=None, overlap=None, since=None, until=None, fields=None,
                        limit=100, offset=None, lat_lon_direction="yx"):
    point = format_polygon(point, lat_lon_direction)
    url = f"{base_url}staticmap/v2/coverage.json?point={point}&radius={radius}"
    if overlap:
        url += f"&overlap={overlap}"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if resources:
        url += f"&resources={resources}"
    if fields:
        url += f"&fields={fields}"
    if limit:
        url += f"&limit={limit}"
    if offset:
        url += f"&offset={offset}"
    url += f"&apikey={api_key}"
    return get(url).json()


def imageStaticMapV2(base_url, api_key, surveyID, image_type, file_format, point, radius, size, transactionToken, out_image,
                     lat_lon_direction="yx"):
    point = format_polygon(point, lat_lon_direction)
    url = f"{base_url}staticmap/v2/surveys/{surveyID}/{image_type}.{file_format}"
    url += f"?point={point}&radius={radius}&size={size}&transactionToken={transactionToken}"
    if not out_image:
        raise Exception("error: Output Image File Path or Bytes flag undefined.")
    if out_image.lower() == "bytes":
        return BytesIO(get(url, stream=True).content)
    else:
        if out_image.endswith(file_format):
            return download_file(url, out_image)
        else:
            raise Exception(f"error: Output image format and selected image format are not consistent {out_image}"
                            f" | {file_format}")


##################
#  NEARMAP Tiles
################


def tileV3(base_url, api_key, tileResourceType, z, x, y, out_format, out_image, tertiary=None, since=None, until=None,
           mosaic=None, include=None, exclude=None):
    if "." in out_format:
        out_format.replace(".", "")
    out_format = out_format.lower().strip()
    tileResourceType = tileResourceType.lower().capitalize().strip()
    url = f"{base_url}tiles/v3/{tileResourceType}/{z}/{x}/{y}.{out_format.lower()}?apikey={api_key}"
    if tertiary:
        url += "&tertiary=satellite"
    if since:
        # TODO: Implement datetime format checker...
        url += f"&since={since}"
    if until:
        # TODO: Implement datetime format checker...
        url += f"&until={until}"
    if mosaic:
        mosaic_options = ["latest", "earliest"]
        if mosaic.lower() in mosaic_options:
            url += f"&mosaic={mosaic.lower()}"
        else:
            raise Exception(f"error: mosaic input string not a member of {mosaic_options}")
    if include:
        # TODO: Assess tag inclusion and auto-formatting json, list, etc into the schema. fun...
        url += f"&include={include}"
    if exclude:
        # TODO: Assess tag exclusion and auto-formatting json, list, etc into the schema. fun....
        url += f"&exclude={exclude}"
    if not out_image:
        raise Exception("error: Output Image File Path or Bytes flag undefined.")
    if out_image.lower() == "bytes":
        return BytesIO(get(url, stream=True).content)
    else:
        if out_image.endswith(out_format):
            open(out_image, 'wb').write(get(url, allow_redirects=True).content)
        else:
            raise Exception(f"error: Output image format and selected image format are not consistent {out_image}"
                            f" | {out_format}")
        return out_image


def tileSurveyV3(base_url, api_key, surveyid, contentType, z, x, y, out_format, out_image):
    if "." in out_format:
        out_format.replace(".", "")
    out_format = out_format.lower().strip()
    contentType = contentType.lower().capitalize().strip()
    url = f"{base_url}tiles/v3/surveys/{surveyid}/{contentType}/{z}/{x}/{y}.{out_format.lower()}?apikey={api_key}"

    if not out_image:
        raise Exception("error: Output Image File Path or Bytes flag undefined.")
    if out_image.lower() == "bytes":
        return BytesIO(get(url, stream=True).content)
    else:
        if out_image.endswith(out_format):
            open(out_image, 'wb').write(get(url, allow_redirects=True).content)
        else:
            raise Exception(f"error: Output image format and selected image format are not consistent {out_image}"
                            f" | {out_format}")
        return out_image
