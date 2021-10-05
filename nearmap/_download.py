####################################
#   File name: _download.py
#   About: The Nearmap API for Python
#   Author: Connor Tluck | Solutions Engineer | Nearmap
#           Geoff Taylor | Sr Solutions Architect | Nearmap
#   Date created: 7/10/2021
#   Last update: 9/28/2021
#   Python Version: 3.6+
####################################

try:
    from ujson import dump, dumps
except ModuleNotFoundError:
    from json import dump, dumps


def process_payload(combined_dataframe, out_folder, out_format, save=True):
    """
    The following function is used to save the AI payload to user local machine
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    combined_dataframe   Required dataframe: input geopandas dataframe which is being processed.
    ---------------     --------------------------------------------------------------------
    out_folder   Required String: Location to save the output files.
    ---------------     --------------------------------------------------------------------
    save                Optional: Toggle to run the function or not and produce save outputs.
    ===============     ====================================================================
    :return: AI feature payload in a geopackage
    """
    import json

    df_features = combined_dataframe
    response = df_features.to_json()

    if save:
        supported_formats = ["gpkg", "json"]
        assert out_format.lower().replace(".", "") in supported_formats, f"Error: Out Format {out_format} not a " \
                                                                         f"member of {supported_formats}"
        if out_format.lower().replace(".", "") == "json":
            with open(f"{out_folder}/ai_download.json", 'w') as f:
                json.dump(response, f)
        elif out_format.lower().replace(".", "") == "gpkg":
            df_features_saveable = (df_features.assign(
                description=df_features.description.astype('str'),
            ))
            if len(df_features) > 1:  # Not just parcel polygon
                df_features_saveable['attributes'] = df_features_saveable.attributes.apply(
                    lambda j: json.dumps(j, indent=2))  # Render attributes as string so it can be saved as a geopackage
            df_features_saveable.to_file(f"{out_folder}/ai_download.gpkg", driver="GPKG")
    return df_features


def process_payload_parse(combined_dataframe, out_folder, out_format, save=True):
    """
    The following function is used to save the AI payload to user local machine, parsed by description
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    combined_dataframe   Required dataframe: input geopandas dataframe which is being processed.
    ---------------     --------------------------------------------------------------------
    out_folder   Required String: Location to save the output files.
    ---------------     --------------------------------------------------------------------
    save                Optional: Toggle to run the function or not and produce save outputs.
    ===============     ====================================================================
    :return: AI feature payload in a geopackage, one unique geopackage per unique feature by description
    """
    import json

    df_features = combined_dataframe

    if save:
        supported_formats = ["gpkg", "json"]
        assert out_format.lower().replace(".", "") in supported_formats, f"Error: Out Format {out_format} not a " \
                                                                         f"member of {supported_formats}"
        feature_divided_dict = {}
        for key in df_features['description'].unique():
            current_key_df = df_features[df_features['description'] == key]
            feature_divided_dict[key] = current_key_df
        if out_format.lower().replace(".", "") == "json":
            for feature in list(df_features.description.unique()):
                parsed_df = df_features[df_features['description'] == feature]
                parsed_json = parsed_df.to_json()
                with open(out_folder + "/ai_download_" + f"{feature}.json", 'w') as f:
                    json.dump(parsed_json, f)
        elif out_format.lower().replace(".", "") == "gpkg":
            for attribute in feature_divided_dict:
                df_features = feature_divided_dict[attribute]
                df_features_saveable = (df_features.assign(
                    description=df_features.description.astype('str'),
                ))
                df_features_saveable['attributes'] = df_features_saveable.attributes.apply(
                    lambda j: json.dumps(j, indent=2))  # Render attributes as string so it can be saved as a geopackage
                df_features_saveable.to_file(out_folder + "/ai_download_" + f"{attribute}.gpkg", driver="GPKG")
    return df_features


def get_parcel_as_geodataframe(payload, parcel_poly):
    """
    The following function is used to process the AI API json output into a geodataframe (geopandas). Deals with
    json response nesting and header creation to set up the geodataframe
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    payload             Required json: input json which is being processed.
    ---------------     --------------------------------------------------------------------
    parcel_poly         Required shapely object: Geometry from the parcel dataframe which to set as the geometry of the
                        the geodataframe row.
    ===============     ====================================================================
    :return: Geodataframe
    """
    import shapely
    import geopandas as gpd
    '''
    Convert each feature in the payload into a row of a geopandas GeoDataFrame, and its attributes as a nested dictionary parsed from the json as an "attributes" column.
    '''
    df_features = [{'geometry': parcel_poly, 'description': 'Parcel Polygon', 'classId': 0, 'link': '',
                    'systemVersion': payload["systemVersion"], 'confidence': 1}]
    for feature in payload['features']:
        poly = shapely.geometry.shape(feature['geometry'])
        feature_tmp = feature.copy()
        feature_tmp['geometry'] = poly

        feature_tmp['parentId'] = str(feature['parentId'])
        feature_tmp['link'] = payload['link']
        feature_tmp['systemVersion'] = payload['systemVersion']
        if 'attributes' in feature:
            feature_tmp['attributes'] = feature['attributes']
        df_features.append(feature_tmp)

    df_features = gpd.GeoDataFrame(df_features, geometry='geometry', crs='EPSG:4326')

    # clean up the descriptions for windows string compatability issues with '>' and '<'
    cleaned_feature_descriptions = []
    for index, row in df_features.iterrows():
        unprocessed_description = row['description']
        processed_description = unprocessed_description.replace('>', 'greater than ').replace('<',
                                                                                              'less than ').replace('/',
                                                                                                                    ' ')
        cleaned_feature_descriptions.append(processed_description)
    df_features['description'] = cleaned_feature_descriptions
    df_features = df_features.sort_values('description')
    return df_features


def generate_ai_pack(base_url, api_key, df_parcels, out_folder, since=None, until=None, packs=None,
                     out_format="json", lat_lon_direction="yx", surveyResourceID=None):

    """
   The following function is the main processing function for the AI data request. The function will take in a user
   request and return saved json or geopackage files.
   Note: See __init__.py.download_ai for full description.
   :return: geopackage of all features as well as geopackage for each individual feature.
   """
    import geopandas as gpd
    from nearmap._api import aiFeaturesV4

    # TODO automatically derive from first feature in json.
    column_names = ['geometry',
                    'description',
                    'classId',
                    'link',
                    'systemVersion',
                    'confidence',
                    'id',
                    'parentId',
                    'areaSqm',
                    'areaSqft',
                    'attributes',
                    'surveyDate',
                    'meshDate']

    full_ai_df = gpd.GeoDataFrame(columns=column_names, crs='EPSG:4326')
    full_ai_df.set_geometry(col='geometry', inplace=True)

    # Specify the AI Packs. This list represents all AI Packs that are currently available.
    for row, column in df_parcels.iterrows():
        if not column.geometry.is_empty:
            # pull the shapely polygon from the current row of grid df
            poly_obj = df_parcels.loc[row, 'geometry']
            # define the polygon being used on the current row
            current_grid = list(poly_obj.exterior.coords)
            polygon = [item for sublist in current_grid for item in sublist]
            # print('THIS IS A POLYGON REQUEST')
            # print(polygon)
            # make request for json data for the formatted polygon
            response = aiFeaturesV4(base_url, api_key, polygon, since, until, packs, out_format="json",
                                    lat_lon_direction="yx")
            # print('THIS IS THE RESPONSE')
            # print(response)
            df_features = get_parcel_as_geodataframe(response, poly_obj)
            full_ai_df = full_ai_df.append(df_features)

    # print(type(full_ai_df))
    full_ai_gdf = gpd.GeoDataFrame(full_ai_df, geometry='geometry')

    process_payload(full_ai_gdf, out_folder, out_format, save=True)
    process_payload_parse(full_ai_gdf, out_folder, out_format, save=True)

    return full_ai_df


def convert(list_to_convert):
    s = [str(i) for i in list_to_convert]  # Converting integer list to string list
    res = str(",".join(s))  # Join list items using join()
    return res


# define some functions for later
def tuple_to_string(unformatted_tuple):
    raw_string = ""
    for i in unformatted_tuple:
        raw_string = raw_string + str(i)
        raw_string = raw_string + ' '
    return raw_string


def get_payload(request_string):
    import requests
    import logging
    '''
    Basic wrapper code to retrieve the JSON payload from the API, and raise an error if no response is given.
    Using urllib3, this also implements exponential backoff and retries for robustness.
    '''
    s = requests.Session()
    response = s.get(request_string, )

    if response.ok:
        logging.info(f'Status Code: {response.status_code}')
        logging.info(f'Status Message: {response.reason}')
        payload = response.json()
        return payload
    else:
        logging.error(f'Status Code: {response.status_code}')
        logging.error(f'Status Message: {response.reason}')
        logging.error(str(response))
        payload = response.content
        logging.error(str(payload))
        return None


def static_image_parameters(gdal_xml, top_left_long_lat, bottom_right_long_lat, out_image, res=False, run_cmd=False):
    """
    The function contains simple parameter processing to take in user input for top of grid square and bottom of
    grid square, convert those coordinates into the python gdal binding requests for gdal translate options.
    """
    from pyproj import Proj, transform, Transformer
    from osgeo import gdal
    from pathlib import Path

    if res is False:
        resolution = .05  # this is a standard high res return
        # TODO: fix resolution
        # print(f"resolution is {resolution}")
    else:
        resolution = res

    # print('Resolution is: ' + str(resolution))

    # First Bounding Box Coordinate, TOP LEFT
    transformer = Transformer.from_crs(4326, 3857, always_xy=True)

    top_left, bottom_right = transformer.itransform([[top_left_long_lat[0], top_left_long_lat[1]],
                                                     [bottom_right_long_lat[0], bottom_right_long_lat[1]]])
    '''
    print(f'top left dimension converted is: {top_left}')
    print(top_left)  # long, lat
    print(f'bottom right dimension converted is: {bottom_right}')
    print(bottom_right)  # long, lat
    '''

    long_difference = bottom_right[0] - top_left[0]
    lat_difference = bottom_right[1] - top_left[1]
    long_pixel_count = abs(long_difference / resolution)
    lat_pixel_count = abs(lat_difference / resolution)
    '''
    print('top left bounding box long and lat is: ' + str(top_left_long_lat))
    print('bottom right bounding box long and lat is: ' + str(bottom_right_long_lat))
    print('bouding box y axis pixel count: ' + str(long_pixel_count))
    print('bouding box x axis pixel count: ' + str(lat_pixel_count))
    
    print('HERE IS YOUR FORMATTED STRING')
    #     print('gdal_translate --debug ON  -a_srs EPSG:3857 -projwin ' + tuple_to_string(top_left_long_lat) + tuple_to_string(bottom_right_long_lat) + '-projwin_srs "EPSG:4326" -outsize ' + str(long_pixel_count) + ' ' +str(lat_pixel_count) + ' tile_dl_blank.xml coltgateway.tif')
    '''
    top_left = tuple_to_string(top_left_long_lat)
    bottom_right = tuple_to_string(bottom_right_long_lat)

    gdal_string = f'gdal_translate --debug ON -a_srs EPSG:3857 -projwin {top_left}{bottom_right}-projwin_srs "EPSG:4326" -outsize {long_pixel_count} {lat_pixel_count} tile_dl.xml {out_image}'  # TODO xml is still being used, need to mvoe and chance the file.
    '''
    print('THIS IS THE GDAL STRING BELOW ME')
    print(gdal_string)
    '''

    format = None
    file_extension = Path(out_image).suffix.replace(".", "")
    if file_extension == "tif":
        format = "Gtiff"
    elif file_extension == "jp2":
        format = "JP2OpenJPEG"
    elif file_extension == "jpg":
        format = "JPEG"
    elif file_extension == "png":
        format = "PNG"
    else:
        print(f"format not detected for {out_image}... currently does not exist in library...")
        exit()
    # this is the gdal translate binding parameters
    projWin = [top_left_long_lat[0], top_left_long_lat[1], bottom_right_long_lat[0], bottom_right_long_lat[1]]
    projWinSRS = "EPSG:4326"
    outputSRS = "EPSG:3857"
    width = lat_pixel_count
    height = long_pixel_count

    if run_cmd is True and format is not None:
        gdal.Translate(out_image, gdal_xml, format=format, width=width, height=height, projWin=projWin,
                       projWinSRS=projWinSRS, outputSRS=outputSRS)
    if format is None:
        print(f"Error: Could not detect output format for image: {out_image}")
    else:
        # print(gdal_string)
        pass


def ortho_imagery_downloader(api_key, df_parcels, out_folder, out_format="tif", tertiary=None, since=None, until=None,
                             mosaic=None, include=None, exclude=None, zoom_level=None):

    """
   The following function is the main processing function for the ortho imagery request. The function will take in a
   user requested area and return saved tifs.
   Note: See __init__.py.ortho_imagery_downloader for full description.
   :return: tif files for each image tile that covers the requested area, user can decide resolution via parameters.
      """
    '''this code generates all static images by hitting the tile api and stitching them together for each grid in the parcel dataframe. uses the command prompt natively, still need to fix for file location selection'''
    from pathlib import Path

    def structure_rest_endpoint(url, tertiary=None, since=None, until=None, mosaic=None, include=None, exclude=None):
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
        return url

    def _update_xml_api_key(xml_file, source_string, replace_string):
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for elem in root.iter('Service'):
            for item in elem.iter('ServerUrl'):
                item.text = item.text.replace(source_string, replace_string)
        tree.write(xml_file)

    def _update_xml_level(xml_file, zoom_level):
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for elem in root.iter('DataWindow'):
            for item in elem.iter('TileLevel'):
                item.text = str(zoom_level)
        tree.write(xml_file)

    out_format = out_format.strip().replace(".", "").lower()

    root_dir = Path(__file__).parent.resolve()
    gdal_xml = f'{root_dir}/tile_dl.xml'
    structured_endpoint = structure_rest_endpoint(api_key, tertiary, since, until, mosaic, include, exclude)
    _update_xml_api_key(xml_file=gdal_xml, source_string="{api_key}", replace_string=structured_endpoint)
    #if not zoom_level:
    #    zoom_level = 21
    # _update_xml_level(xml_file=gdal_xml, zoom_level=zoom_level)

    fail_list = []
    num_tiles = df_parcels.shape[0]
    tile_intervals = []
    if num_tiles > 20:
        tile_intervals = [i for i in range(0, num_tiles, int(num_tiles*.05))]
    for row, column in df_parcels.iterrows():
        if not column.geometry.is_empty:
            top_left_long_lat = list(df_parcels.tile[row].exterior.coords[0])
            bottom_right_long_lat = list(df_parcels.tile[row].exterior.coords[2])

            static_image_name = out_folder + f'/ortho_{row}.{out_format}'
            #try:
            static_image_parameters(gdal_xml, top_left_long_lat, bottom_right_long_lat, static_image_name,
                                    res=False, run_cmd=True)
            #except:  # TODO: exception currently not working for error... determine how to return error in exception
            '''ERROR 1: GDALWMS: Unable to download block 143053, 222760.
                URL:
                  HTTP status code: 504, error: (null).
                Add the HTTP status code to <ZeroBlockHttpCodes> to ignore this error (see http://www.gdal.org/frmt_wms.html).
                ERROR 1: IReadBlock failed at X offset 143051, Y offset 222758: GDALWMS: Unable to download block 143053, 222760'''
            #print("Error: Could not retrieve/process tile at this time... will re-attempt later in process")
            #fail_list.append([row, top_left_long_lat, bottom_right_long_lat, static_image_name])
            if row in tile_intervals and num_tiles > 20:  # Print Percentage complete in intervals of 5
                print(f"{tile_intervals.index(row)*5}% Complete")
    for i in fail_list:  # Process Tiles that did not initially process due to errors...
        static_image_parameters(gdal_xml, i[1], i[2], i[3], res=False, run_cmd=True)

    structure_rest_endpoint(api_key, tertiary, since, until, mosaic, include, exclude)
    _update_xml_api_key(xml_file=gdal_xml, source_string=structured_endpoint, replace_string="{api_key}")
    #if zoom_level != 21:
        # _update_xml_level(xml_file=gdal_xml, zoom_level=zoom_level)
    return


def dsm_imagery_downloader(base_url, api_key, df_parcels, out_folder, since=None, until=None, fields=None):
    """
        main function to handle DSM content downloads.
        ================    ===============================================================
        Note: See __init__.py.dsm_imagery_downloader for full description.
        ================    ===============================================================
    """
    from nearmap._api import coverageStaticMapV2
    from nearmap._api import imageStaticMapV2

    for row, column in df_parcels.iterrows():

        if column.geometry.is_empty:
            # print('this was empty')
            pass

        else:
            x = df_parcels.iloc[row].tile.centroid.coords[:]  # raw centroid point in a list of tuples
            # print("DSM data is being Returned....")
            # center_point_of_grid = str(x[0][0]) + ',' + str(x[0][1]) #unpack raw centroid coords into a string for the API call.

            point = [x[0][0], x[0][1]]
            radius = 100
            resources = "DetailDsm"

            coverage = coverageStaticMapV2(base_url, api_key, point=point, radius=radius, resources=resources,
                                           overlap=None, since=since, until=until, fields=fields, limit=100,
                                           offset=None, lat_lon_direction="yx")
            transactionToken = coverage["transactionToken"]
            most_recent_survey_id = coverage["surveys"][0]["id"]  # Gets most recent surveyID
            tif_save_path = out_folder + '/DSM_' + 'Grid_Number_' + str(row) + '.tif'
            imageStaticMapV2(base_url, api_key, surveyID=most_recent_survey_id, image_type=resources, file_format='tif',
                             point=point, radius=radius, size="5000x5000",
                             transactionToken=transactionToken,
                             out_image=tif_save_path)
