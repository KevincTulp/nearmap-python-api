####################################
#   File name: __init__.py
#   About: The Nearmap API for Python
#   Authors: Geoff Taylor | Sr Solution Architect | Nearmap
#            Connor Tluck | Solutions Engineer | Nearmap
#   Date created: 7/7/2021
#   Last update: 1/03/2022
#   Python Version: 3.8+
####################################

from datetime import datetime, timezone, timedelta
from requests import get
from io import BytesIO
from time import sleep
from pathlib import Path
from os import mkdir
from os.path import splitext
from re import sub

try:
    from ujson import loads, dumps
except ModuleNotFoundError:
    from json import loads, dumps


def _create_folder(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _format_polygon(polygon, lat_lon_direction):
    if type(polygon) is str:
        polygon = [float(i) for i in polygon.split(",")]
    assert (len(polygon) % 2) == 0, "Error: input geometry does not contain an even number of lat/lon coords"
    if lat_lon_direction.lower() == "xy":
        polygon = polygon.reverse()
    return str(polygon)[1:-1].replace(" ", "")


def _download_file(url, out_file):
    r = get(url, stream=True)
    # print(r.headers)
    if r.status_code == 200:
        with open(out_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return out_file
    else:
        print(_http_response_error_reporting(r.status_code))


def _get_image(url, out_format, out_image, rate_limit_mode="slow", quiet=False):
    def _image_get_op(url, out_format, out_image):
        iter = 1
        if out_image.lower() == "bytes":
            return get(url, stream=True)
        else:
            assert out_image.endswith(
                out_format), f"Error, output image {out_image} does not end with format {out_format}"
            data = None
            while data is None:
                try:
                    data = get(url, allow_redirects=True)
                    return data
                    # return get(url, allow_redirects=True)
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
                    backoff_time = iter * 0.03
                    if backoff_time >= 1800:
                        sleep(backoff_time)
                        iter = 1
                    sleep(backoff_time)
                    iter += 1

    img_formats = ["jpg", "png", "img"]
    assert out_format in img_formats, f"Error, output image format must be a member of {','.join(img_formats)}"
    assert out_image, "error: Output Image File Path or Bytes flag undefined."

    image = None
    iter = 1
    image = _image_get_op(url, out_format, out_image)
    response_code = image.status_code
    if response_code != 200:
        # pass
        if not quiet:
            print(_http_response_error_reporting(response_code))
    if response_code == 404:
        return None
    # Begin Rate Limiting if response = 429
    # if response_code == 429:  # If user hits default rate limit pause for milliseconds.
    if response_code == 429 or str(response_code)[:1] == "5":
        sleep(0.1)
        image = _image_get_op(url, out_format, out_image)
        response_code = image.status_code
    # if response_code == 429:  # If rate limit is still hit implement slow or fast rate_limit_mode
    if response_code == 429 or str(response_code)[:1] == "5":
        rate_limit_modes = ["slow", "fast"]
        assert rate_limit_mode.lower() in rate_limit_modes, f"Error: Rate_limit_mode not a member of " \
                                                            f"{','.join(rate_limit_modes)}"
        if rate_limit_mode.lower() == "slow":
            while response_code == 429:
                rate_limit = image.headers["x-ratelimit-limit"]
                rate_limit_reset = image.headers["x-ratelimit-reset"]
                then_utc = datetime.fromtimestamp(float(rate_limit_reset), timezone.utc)
                now_utc = datetime.now(timezone.utc)
                delay_time = abs((now_utc - then_utc) / timedelta(seconds=1)) + 1
                if not quiet:
                    print(f"Rate Limit Exceeded. Reached hourly limit of {rate_limit}. Begin Throttling for "
                          f"{delay_time} seconds")
                sleep(delay_time)
                image = _image_get_op(url, out_format, out_image)
                response_code = image.status_code

        elif rate_limit_mode.lower() == "fast":
            delay_time = 0.3  # 0.3 seconds
            max_delay_time = 1800  # 30 minutes
            while response_code == 429:
                rate_limit = image.headers["x-ratelimit-limit"]
                if not quiet:
                    print(f"Rate Limit Exceeded. Reached hourly limit of {rate_limit}. Begin Throttling for "
                          f"{delay_time} seconds")
                sleep(delay_time)
                image = _image_get_op(url, out_format, out_image)
                response_code = image.status_code
                if delay_time != max_delay_time:  # Incremental Delay increase
                    delay_time *= 2
                elif delay_time >= max_delay_time:  # Cap delay time at 60 seconds
                    delay_time = max_delay_time
    if out_image.lower() == "bytes":
        return BytesIO(image.content)
    else:
        image_format = image.headers.get('Content-Type').replace('image/', '')
        base_path = out_image.replace('.img', '')
        if image_format == "jpeg":
            path = f'{base_path}.jpg'
        elif image_format == "png":
            path = f'{base_path}.png'
        # source_format = Path(out_image)
        open(path, 'wb').write(image.content)
        return path


def _http_response_error_reporting(status):
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
        return '429 Too Many Requests: The rate limit has been reached...'
    elif str(status)[:1] == "5":
        return f"{status} Server Error. Returned when something is wrong in the server side."
    else:
        return f"{status} Unknown Error..."


####################
# Download Features
###################


def download_ortho(api_key, polygon, out_folder, out_format="tif", tertiary=None, since=None, until=None, mosaic=None,
                   include=None, exclude=None, res=None, zoom_level=None):
    from nearmap._download_lib import get_coords, create_grid, grid_to_slippy_grid, generate_static_images
    from nearmap._download import ortho_imagery_downloader

    coords = get_coords(in_file=polygon)
    grid = create_grid(coords)
    slippy_grid = grid_to_slippy_grid(in_polygon_coords=coords, in_grid=grid)
    Path(out_folder).mkdir(parents=True, exist_ok=True)
    ortho_out = ortho_imagery_downloader(api_key, slippy_grid, out_folder, out_format, tertiary, since, until, mosaic,
                                         include, exclude, res, zoom_level)
    return slippy_grid, ortho_out


def download_dsm(base_url, api_key, polygon, out_folder, since=None, until=None, fields=None):
    from nearmap._download_lib import get_coords, create_grid, grid_to_slippy_grid, generate_static_images
    from nearmap._download import dsm_imagery_downloader

    coords = get_coords(in_file=polygon)
    grid = create_grid(coords)
    slippy_grid = grid_to_slippy_grid(in_polygon_coords=coords, in_grid=grid)
    Path(out_folder).mkdir(parents=True, exist_ok=True)
    dsm_out = dsm_imagery_downloader(base_url, api_key, slippy_grid, out_folder, since, until, fields)
    return slippy_grid, dsm_out


def download_ai(base_url, api_key, polygon, out_folder, since=None, until=None, packs=None, out_format="json",
                lat_lon_direction="yx", surveyResourceID=None):
    from nearmap._download_lib import get_coords, create_grid, grid_to_slippy_grid, generate_static_images
    from nearmap._download import generate_ai_pack, process_payload, process_payload_parse

    coords = get_coords(in_file=polygon)
    grid = create_grid(coords)
    slippy_grid = grid_to_slippy_grid(in_polygon_coords=coords, in_grid=grid)
    Path(out_folder).mkdir(parents=True, exist_ok=True)
    ai_out = generate_ai_pack(base_url, api_key, slippy_grid, out_folder, since, until, packs, out_format,
                              lat_lon_direction, surveyResourceID)
    return slippy_grid, ai_out


def download_multi(base_url, api_key, polygon, out_folder, tertiary=None, since=None, until=None, mosaic=None,
                   include=None, exclude=None, packs=None, out_ai_format="json", out_ortho_format="json",
                   lat_lon_direction="yx", surveyResourceID=None):
    from nearmap._download import ortho_imagery_downloader, dsm_imagery_downloader, generate_ai_pack
    from nearmap._download_lib import get_coords, create_grid, grid_to_slippy_grid

    coords = get_coords(in_file=polygon)
    grid = create_grid(coords)
    slippy_grid = grid_to_slippy_grid(in_polygon_coords=coords, in_grid=grid)
    Path(out_folder).mkdir(parents=True, exist_ok=True)
    ortho_out_folder = f"{out_folder}/ortho"
    Path(ortho_out_folder).mkdir(parents=True, exist_ok=True)
    print("Downloading Ortho Imagery")

    ortho_out = ortho_imagery_downloader(api_key, slippy_grid, ortho_out_folder, out_ortho_format, tertiary, since,
                                         until, mosaic, include, exclude)
    dsm_out_folder = f"{out_folder}/dsm"
    Path(dsm_out_folder).mkdir(parents=True, exist_ok=True)
    print("Downloading DSM (Digital Surface Model) Data")
    dsm_out = dsm_imagery_downloader(base_url, api_key, slippy_grid, dsm_out_folder, since, until)
    ai_out_folder = f"{out_folder}/ai_packs"
    Path(ai_out_folder).mkdir(parents=True, exist_ok=True)
    print("Downloading AP Packs")
    ai_out = generate_ai_pack(base_url, api_key, slippy_grid, ai_out_folder, since, until, packs, out_ai_format,
                              lat_lon_direction, surveyResourceID)

    return slippy_grid, ortho_out, dsm_out, ai_out


###############
#  NEARMAP AI
#############


def aiFeaturesV4(base_url, api_key, polygon, since=None, until=None, packs=None, out_format="json", output=None,
                 lat_lon_direction="yx", surveyResourceID=None, return_url=False):
    url = str()
    if not return_url:
        polygon = _format_polygon(polygon, lat_lon_direction)
        # TODO: determine how to implement surveyResourceID parameter
        url = f"{base_url}ai/features/v4/features.json?polygon={polygon.replace(' ', '')}"
    elif return_url:
        url = f"{base_url}" + "ai/features/v4/features.json?polygon={polygon}"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if packs:
        if not return_url:
            if type(packs) == list:
                f_packs = ','.join(packs)
            else:
                f_packs = packs
                packs = packs.split(",")
            url += f"&packs={f_packs}"

        else:
            url += "&packs={packs}"
    if surveyResourceID:
        if not return_url:
            url += f"&surveyResourceId={surveyResourceID}"
        else:
            url += "&surveyResourceId={surveyResourceID}"
    if not return_url:
        url += f"&apikey={api_key}"
    else:
        url += "&apikey={api_key}"

    supported_df_formats = ["pandas", "pd"]
    supported_spreadsheet_formats = ["csv", "xlsx", "parquet"]
    supported_geo_file_formats = ["geojson", "shp"]
    supported_gdf_formats = ["geopandas", "gpd"]
    supported_db_formats = ["gpkg", "gdb"]
    if out_format == "json":
        if not return_url:
            return get(url).json()
        elif return_url:
            return "f'" + url + "'"
    all_supported_formats = []
    [all_supported_formats.extend(_) for _ in [supported_df_formats,
                                               supported_spreadsheet_formats,
                                               supported_gdf_formats,
                                               supported_geo_file_formats,
                                               supported_db_formats]]

    if out_format in all_supported_formats:
        output = Path(output)
        assert output, f"Error: no 'output' directory or 'file' specified"
        f_split = splitext(output)
        is_file = False
        is_dir = False
        if not f_split[1]:
            is_dir = True
        elif f_split[1]:
            is_file = True

        if type(packs).__name__ != 'list':
            if type(packs).__name__ == "string":
                packs = [packs]
            else:
                packs = [None]

        if is_file and out_format not in supported_db_formats:
            assert len(packs) == 1 and None not in packs, f"Error: Cannot Download Multiple AI Packs into Single " \
                                                          f"{out_format} file. Output to Folder/Directory instead"
        if is_dir:
            _create_folder(output)

        import geopandas as gpd
        import pandas as pd
        from shapely import geometry
        my_json = get(url).json().get('features')
        column_names = []
        for f in my_json:
            [column_names.append(i) for i in f.keys() if i not in column_names]
        features_list = list()
        for f in my_json:
            temp_dict = dict()
            temp_dict['geometry'] = geometry.shape(f.get('geometry'))
            for k in f.keys():
                if k in column_names:
                    if k not in ['attributes', 'geometry', 'components', 'confidence', 'fidelity']:
                        temp_dict[k] = f.get(k)
                    if k in ['confidence', 'fidelity']:
                        v = f.get(k)
                        if v:
                            temp_dict[k] = round(v, 3)
                        else:
                            temp_dict[k] = v
                    if 'attributes' in f.keys():
                        attrs = f.get('attributes')
                        if len(attrs) > 0:
                            for attr_k in attrs[0].keys():
                                if attr_k not in ['components', 'numStories', 'height', 'description']:
                                    temp_dict[attr_k] = attrs[0].get(attr_k)
                                if attr_k == 'description':
                                    temp_dict['attr_desc'] = attrs[0].get(attr_k)
                                if attr_k == 'components':
                                    components = attrs[0].get(attr_k)
                                    c_count = 0
                                    for c in components:
                                        for c_k in c.keys():
                                            temp_dict[f"comp{c_count}_{c_k}"] = components[c_count].get(c_k)
                                        c_count += 1
                                if attr_k == 'height':
                                    temp_dict['heightMeters'] = round(attrs[0].get(attr_k), 3)
                                    temp_dict['heightFeet'] = round(float(attrs[0].get(attr_k)) * 3.281, 3)
                                if attr_k == 'numStories':
                                    e = dict(sorted(attrs[0].get(attr_k).items(), key=lambda item: item[1],
                                                    reverse=True))
                                    top_story = int(list(e.keys())[0].replace('+', ''))
                                    temp_dict['numStories'] = top_story
                                    v = attrs[0].get(attr_k).get(f'{top_story}')
                                    if v:
                                        temp_dict['numStorConfidence'] = round(v, 3)
                                    else:
                                        temp_dict['numStorConfidence'] = None
            features_list.append(temp_dict)
        #exit()
        if not features_list:
            print(f"Error: No Features Detected for AI Pack '{packs}'")
            return None
        else:
            gdf = gpd.GeoDataFrame(features_list, geometry='geometry', crs='EPSG:4326')
            if out_format in supported_df_formats or out_format in supported_spreadsheet_formats:
                df = pd.DataFrame(gdf)
                if out_format in ["pandas", "pd"]:
                    return df
                elif out_format == "parquet":
                    df.to_parquet(output)
                elif out_format == "feather":
                    df.to_feature(output)
                elif out_format == "csv":
                    df.to_csv(output, index=False)
                elif out_format == "xlsx":
                    df.to_excel(output)
                    #df.to_excel(output, engine='xlsxwriter')
            if out_format in supported_gdf_formats:
                return gdf
            elif out_format == "geojson" and output is None:
                return gdf.to_json()
            elif out_format in supported_geo_file_formats or out_format in supported_db_formats:
                packs_keys = gdf['description'].unique()
                gdf_dict = dict()
                #gdf_columns = list(gdf.columns)
                for _ in packs_keys:
                    gdf_dict[_] = gdf.loc[gdf['description'] == _].dropna(axis=1)
                output = Path(output)
                for key, subset_gdf in gdf_dict.items():
                    name = sub('[\W_]+', '', key).strip()
                    f = output
                    if is_dir:
                        if out_format in supported_geo_file_formats:
                            f = (output / f"{name}.{out_format}").as_posix()
                        elif out_format in supported_db_formats:
                            f = output / f"nearmap.{out_format}"
                    if out_format == "geojson":
                        subset_gdf.to_file(f, driver='GeoJSON')
                    if out_format == "shp":
                        subset_gdf.to_file(f)
                    elif out_format == "gpkg":
                        subset_gdf.to_file(f, driver="GPKG", layer=name)
                return output
    else:
        print(f"Error: output out_format {out_format} is not supported.")
        exit()


def aiClassesV4(base_url, api_key, out_format="json", return_url=False):
    url = str()
    if not return_url:
        url = f"{base_url}ai/features/v4/classes.json?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "ai/features/v4/classes.json?apikey={api_key}"
    if out_format.lower() in ["pandas", "pd"]:
        import pandas as pd
        return pd.read_json(url)
    elif out_format.lower() == "text":
        return get(url).text
    elif out_format.lower() == "json":
        if not return_url:
            return get(url).json()
        elif return_url:
            return "f'" + url + "'"
    else:
        print(f"Error: output format {out_format} not a viable option")
        exit()


def aiPacksV4(base_url, api_key, out_format="json", return_url=False):
    url = str()
    if not return_url:
        url = f"{base_url}ai/features/v4/packs.json?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "ai/features/v4/packs.json?apikey={api_key}"
    if out_format.lower() in ["pandas", "pd"]:
        import pandas as pd
        return pd.read_json(url)
    elif out_format.lower() == "text":
        return get(url).text
    elif out_format.lower() == "json":
        if not return_url:
            return get(url).json()
        elif return_url:
            return "f'" + url + "'"
    else:
        print(f"Error: output format {out_format} not a viable option")
        exit()


#####################
#  NEARMAP Coverage
###################


def polyV2(base_url, api_key, polygon, since=None, until=None, limit=20, offset=None, fields=None, sort=None,
           overlap=None, include=None, exclude=None, lat_lon_direction="yx", return_url=False):
    url = str()
    if return_url is False:
        polygon = _format_polygon(polygon, lat_lon_direction)
        url = f"{base_url}coverage/v2/poly/{polygon}"
        url += f"?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "coverage/v2/poly/{polygon}?apikey={api_key}"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if limit:
        if not return_url:
            url += f"&limit={limit}"
        else:
            url += "&limit={limit}"
    if offset:
        if not return_url:
            url += f"&offset={offset}"
        else:
            url += "&offset={offset}"
    if fields:
        if not return_url:
            url += f"&fields={fields}"
        else:
            url += "&fields={fields}"
    if sort:
        if not return_url:
            url += f"&sort={sort}"
        else:
            url += "&sort={sort}"
    if overlap:
        if not return_url:
            url += f"&overlap={overlap}"
        else:
            url += "&overlap={overlap}"
    if include:
        if not return_url:
            url += f"&include={include}"
        else:
            url += "&include={include}"
    if exclude:
        if not return_url:
            url += f"&exclude={exclude}"
        else:
            url += "&exclude={exclude}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        e = get(url)
        if e.status_code != 200:
            print(e)
        return e.json()


def pointV2(base_url, api_key, point, since=None, until=None, limit=20, offset=None, fields=None, sort=None,
            include=None, exclude=None, lat_lon_direction="yx", return_url=False):
    url = str()
    point = _format_polygon(point, lat_lon_direction)
    if not return_url:
        url = f"{base_url}coverage/v2/point/{point}?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "coverage/v2/point/{point}?apikey={api_key}"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if limit:
        if not return_url:
            url += f"&limit={limit}"
        else:
            url += "&limit={limit}"
    if offset:
        if not return_url:
            url += f"&offset={offset}"
        else:
            url += "&offset={offset}"
    if fields:
        if not return_url:
            url += f"&fields={fields}"
        else:
            url += "&fields={fields}"
    if sort:
        if not return_url:
            url += f"&sort={sort}"
        else:
            url += "&sort={sort}"
    if include:
        if not return_url:
            url += f"&include={include}"
        else:
            url += "&include={include}"
    if exclude:
        if not return_url:
            url += f"&exclude={exclude}"
        else:
            url += "&exclude={exclude}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        e = get(url)
        if e.status_code != 200:
            print(e)
        return e.json()


def coordV2(base_url, api_key, z, x, y, since=None, until=None, limit=20, offset=None, fields=None, sort=None,
            include=None, exclude=None, return_url=False):
    url = str()
    if not return_url:
        url = f"{base_url}coverage/v2/coord/{z}/{x}/{y}?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "coverage/v2/coord/{z}/{x}/{y}?apikey={api_key}"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if limit:
        if not return_url:
            url += f"&limit={limit}"
        else:
            url += "&limit={limit}"
    if offset:
        if not return_url:
            url += f"&offset={offset}"
        else:
            url += "&offset={offset}"
    if fields:
        if not return_url:
            url += f"&fields={fields}"
        else:
            url += "&fields={fields}"
    if sort:
        if not return_url:
            url += f"&sort={sort}"
        else:
            url += "&sort={sort}"
    if include:
        if not return_url:
            url += f"&include={include}"
        else:
            url += "&include={include}"
    if exclude:
        if not return_url:
            url += f"&exclude={exclude}"
        else:
            url += "&exclude={exclude}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        e = get(url)
        if e.status_code != 200:
            print(e)
        return e.json()


def surveyV2(base_url, api_key, polygon, fileFormat="geojson", since=None, until=None, limit=20, offset=None,
             resources=None, overlap=None, include=None, exclude=None, lat_lon_direction="yx", return_url=False):
    url = str()
    if not return_url:
        polygon = _format_polygon(polygon, lat_lon_direction)
        url = f"{base_url}coverage/v2/surveyresources/boundaries.{fileFormat}?polygon={polygon}&apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "coverage/v2/surveyresources/boundaries.{fileFormat}?polygon={polygon}&apikey={api_key}"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if limit:
        if not return_url:
            url += f"&limit={limit}"
        else:
            url += "&limit={limit}"
    if offset:
        if not return_url:
            url += f"&offset={offset}"
        else:
            url += "&offset={offset}"
    if resources:
        if not return_url:
            url += f"&resources={resources}"
        else:
            url += "&resources={resources}"
    if overlap:
        if not return_url:
            url += f"&overlap={overlap}"
        else:
            url += "&overlap={overlap}"
    if include:
        if not return_url:
            url += f"&include={include}"
        else:
            url += "&include={include}"
    if exclude:
        if not return_url:
            url += f"&exclude={exclude}"
        else:
            url += "&exclude={exclude}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        return get(url).json()


def coverageV2(base_url, api_key, fileFormat="geojson", types=None, return_url=False):
    url = str()
    if not return_url:
        url = f"{base_url}coverage/v2/aggregate/boundaries.{fileFormat}?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "coverage/v2/aggregate/boundaries.{fileFormat}?apikey={api_key}"
    if types:
        if not return_url:
            url += f"&types={types}"
        else:
            url += "&types={types}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        return get(url).json()


###############################
# NEARMAP DSM & TrueOrtho API
#############################


def coverageStaticMapV2(base_url, api_key, point, radius, resources=None, overlap=None, since=None, until=None,
                        fields=None, limit=100, offset=None, lat_lon_direction="yx", return_url=False):
    url = str()
    if not return_url:
        point = _format_polygon(point, lat_lon_direction)
        url = f"{base_url}staticmap/v2/coverage.json?point={point}&radius={radius}"
    elif return_url:
        url = f"{base_url}" + "staticmap/v2/coverage.json?point={point}&radius={radius}"
    if overlap:
        if not return_url:
            url += f"&overlap={overlap}"
        else:
            url += "&overlap={overlap}"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if resources:
        if not return_url:
            url += f"&resources={resources}"
        else:
            url += "&resources={resources}"
    if fields:
        if not return_url:
            url += f"&fields={fields}"
        else:
            url += "&fields={fields}"
    if limit:
        if not return_url:
            url += f"&limit={limit}"
        else:
            url += "&limit={limit}"
    if offset:
        if not return_url:
            url += f"&offset={offset}"
        else:
            url += "&offset={offset}"
    if not return_url:
        url += f"&apikey={api_key}"
    else:
        url += "&apikey={api_key}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        return get(url).json()


def imageStaticMapV2(base_url, surveyID, image_type, file_format, point, radius, size, transactionToken, out_image,
                     lat_lon_direction="yx", return_url=False):
    url = str()
    if return_url:
        url = f"{base_url}" + "staticmap/v2/surveys/{surveyID}/{image_type}.{file_format}?point={point}" \
                              "&radius={radius}&size={size}&transactionToken={transactionToken}"
        return "f'" + url + "'"
    elif not return_url:
        point = _format_polygon(point, lat_lon_direction)
        url = f"{base_url}staticmap/v2/surveys/{surveyID}/{image_type}.{file_format}"
        url += f"?point={point}&radius={radius}&size={size}&transactionToken={transactionToken}"
    if not out_image:
        raise Exception("error: Output Image File Path or Bytes flag undefined.")
    if out_image.lower() == "bytes":
        return BytesIO(get(url, stream=True).content)
    else:
        if out_image.endswith(file_format):
            return _download_file(url, out_image)
        else:
            raise Exception(f"error: Output image format and selected image format are not consistent {out_image}"
                            f" | {file_format}")


##################
#  NEARMAP Tiles
################


def tileV3(base_url, api_key, tileResourceType, z, x, y, out_format, out_image, tertiary=None, since=None, until=None,
           mosaic=None, include=None, exclude=None, rate_limit_mode="slow", return_url=False):
    url = str()
    if not return_url:
        if "." in out_format:
            out_format.replace(".", "")
        out_format = out_format.lower().strip()
        tileResourceType = tileResourceType.lower().capitalize().strip()
        url = f"{base_url}tiles/v3/{tileResourceType}/{z}/{x}/{y}.{out_format.lower()}?apikey={api_key}"
    elif return_url:
        url = f"{base_url}" + "tiles/v3/{tileResourceType}/{z}/{x}/{y}.{out_format.lower()}?apikey={api_key}"
    if tertiary:
        url += "&tertiary=satellite"
    if since:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&since={since}"
        else:
            url += "&since={since}"
    if until:
        if not return_url:
            # TODO: Implement datetime format checker...
            url += f"&until={until}"
        else:
            url += "&until={until}"
    if mosaic:
        if not return_url:
            mosaic_options = ["latest", "earliest"]
            if mosaic.lower() in mosaic_options:
                url += f"&mosaic={mosaic.lower()}"
            else:
                raise Exception(f"error: mosaic input string not a member of {mosaic_options}")
        else:
            url += "&mosaic={mosaic}"
    if include:
        if not return_url:
            # TODO: Assess tag inclusion and auto-formatting json, list, etc into the schema. fun...
            url += f"&include={include}"
        else:
            url += "&include={include}"
    if exclude:
        if not return_url:
            # TODO: Assess tag exclusion and auto-formatting json, list, etc into the schema. fun....
            url += f"&exclude={exclude}"
        else:
            url += "&exclude={exclude}"
    if return_url:
        return "f'" + url + "'"
    elif not return_url:
        return _get_image(url, out_format, out_image, rate_limit_mode)


def tileSurveyV3(base_url, api_key, surveyid, contentType, z, x, y, out_format, out_image, rate_limit_mode="slow",
                 return_url=False):
    if return_url:
        url = f"{base_url}" + "tiles/v3/surveys/{surveyid}/{contentType}/{z}/{x}/{y}.{out_format.lower()}" \
                              "?apikey={api_key}"
        return "f'" + url + "'"
    elif not return_url:
        if "." in out_format:
            out_format.replace(".", "")
        out_format = out_format.lower().strip()
        contentType = contentType.lower().capitalize().strip()
        url = f"{base_url}tiles/v3/surveys/{surveyid}/{contentType}/{z}/{x}/{y}.{out_format.lower()}?apikey={api_key}"
        return _get_image(url, out_format, out_image, rate_limit_mode)
