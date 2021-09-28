####################################
#   File name: _download.py
#   About: The Nearmap API for Python
#   Author: Connor Tluck | Solutions Engineer | Nearmap
#           Geoff Taylor | Sr Solutions Architect | Nearmap
#   Date created: 7/10/2021
#   Last update: 9/28/2021
#   Python Version: 3.6+
####################################

from zipfile import ZipFile
import xml.etree.ElementTree as ET
import math
from os.path import split
import pandas as pd
from shapely.geometry import Polygon
from pyproj import Proj, transform

try:
    from ujson import loads
except ModuleNotFoundError:
    from json import loads


def _nest_level(lst):
    if not isinstance(lst, list):
        return 0
    if not lst:
        return 1
    return max(_nest_level(lst[0]) + 1, _nest_level(lst[1:]))


def get_shp_coords(in_shp):
    """
    The following function obtains coordinates from a shapefile
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    in_file             Required String:    File Input
                        Supported File formats are:
                            - .shp
    ===============     ====================================================================
    :return: list of geometry coordinates
    """
    try:
        import fiona
        coords = []
        with fiona.open(in_shp) as c:
            for i, record in enumerate(c):
                coords.append(record['geometry']['coordinates'][0])
        return coords
    except ModuleNotFoundError:
        print("Shapefile processing requires Fiona: https://github.com/Toblerity/Fiona | Library not detected")
        exit()


def get_feature_class_coords(in_feature_class):
    """
    The following function obtains coordinates from a feature class within a file geodatabase .gdb
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    in_file             Required String:    File Input
                        Supported File formats are:
                            - .gdb/myFeatureClassName
    ===============     ====================================================================
    :return: list of geometry coordinates
    """
    try:
        import fiona
        coords = []
        # head and tail pair
        gdb, fc = split(in_feature_class)
        with fiona.open(gdb, layer=fc) as c:
            for i, record in enumerate(c):
                coords.append(record['geometry']['coordinates'][0][0])
        return coords
    except ModuleNotFoundError:
        print("FeatureClass processing requires Fiona: https://github.com/Toblerity/Fiona | Library not detected")
        exit()


def get_json_coords(in_json):
    """
    The following function obtains coordinates from json and geojson files
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    in_file             Required String:    File Input
                        Supported File formats are:
                            -json
    ===============     ====================================================================
    :return: list of geometry coordinates
    """
    with open(in_json, 'r') as f:
        data = f.read()
    obj = loads(data)
    try:  # Check for geoJSON and process if geoJSON
        # features = obj["features"][0]["geometry"]["coordinates"] #old code returned error
        features = [tuple(x) for x in obj["features"][0]["geometry"]["coordinates"][0]] #returns in form: [(-72.6639175415039, 41.759131982892384), (-72.6665997505188, 41.7591479892674)...
        return features
    except KeyError as e:  # Input is Standard JSON
        if str(e).lower().replace("'", "") == "coordinates":
            try:
                spatial_ref = obj["spatialReference"]["wkid"]
                if spatial_ref == 4326:
                    features = obj["features"][0]["geometry"]["rings"]
                    return features
                else:
                    print(f"Input JSON spatial reference must be WGS84 wkid 4326. Detected {spatial_ref} instead...")
                    exit()
            except KeyError as e:
                print(f"Could not detect spatial reference in json file | {e}")
                exit()


def get_kml_coords(in_file):
    """
    The following function obtains coordinates from kml and kmz files
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    in_file             Required String:    File Input
                        Supported File formats are:
                            -KMZ
                            -KML
    ===============     ====================================================================
    :return: list of geometry coordinates
    """
    kml = in_file
    if in_file.endswith("kmz"):
        kmz = ZipFile(in_file, 'r')
        kml = kmz.open('doc.kml', 'r')
    root = ET.parse(kml).getroot()
    coord_list = []
    for description in root.iter('{http://www.opengis.net/kml/2.2}coordinates'):
        coords = [float(i) for i in description.text.strip().replace("0 ", "").split(",")]
        if coords[-1] == 0:
            del coords[-1]
        coord_list.append(list(zip(coords[::2], coords[1::2])))
    return coord_list


def get_coords(in_file):
    """
    The following function obtains coordinates from the input feature types
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    in_file             Required String:    File Input
                        Supported file formats are::
                            -Standard JSON
                            -GeoJSON
                            -KMZ
                            -KML
    ===============     ====================================================================
    :return: list of geometry coordinates
    """
    if in_file.endswith("json"):
        return get_json_coords(in_json=in_file)
    elif in_file.endswith(tuple(["kmz", "kml"])):
        return get_kml_coords(in_file=in_file)
    elif ".shp" in in_file:
        return get_shp_coords(in_shp=in_file)
    elif ".gdb" in in_file:
        return get_feature_class_coords(in_feature_class=in_file)
    else:
        print(f"file format {in_file} not supported...")


def create_grid(in_polygon):  # Create Grid Row
    """
    The following function generates a unit grid. This grid has a defined standard grid size as well as a standard
    grid shift. This grid is used to make API calls that are an acceptable size. The sizing is somewhat arbitrary but
    falls within the allowable size restrictions of the AI and DSM apis.
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    in_polygon          Required list:  Required list of coords for a single polygon.
    ===============     ====================================================================
    :return: list of grid coords
    """

    # create unit box move equations to help make the grid once we create our first grid square.
    def _unit_box_move_x(grid_box, x_number=0):
        # unit box shift
        delta_x = (72.6685631 - 72.6661572) * x_number
        right_shift_output_box = []
        for coordinate in grid_box:
            right_shift_output_box.append((coordinate[0] + delta_x, coordinate[1]))
        return right_shift_output_box

    def _unit_box_move_y(grid_box, y_number=0):
        # unit box shift
        delta_y = (41.7575483 - 41.7557535) * y_number
        down_shift_output_box = []
        for coordinate in grid_box:
            down_shift_output_box.append((coordinate[0], coordinate[1] - delta_y))
        return down_shift_output_box

    list_of_x = []
    list_of_y = []
    grid = []
    nesting_level = _nest_level(in_polygon)
    assert nesting_level in [2, 1], "Error, input polygon cannot be read."
    if nesting_level == 2:
        feature_count = len(in_polygon)
        assert feature_count == 1, f"Error, process only supports a single polygon... detected {feature_count} polygons"
        for geom in in_polygon:
            for coord in geom:
                list_of_x.append(coord[0])
                list_of_y.append(coord[1])
    elif nesting_level == 1:
        for coord in in_polygon:
            list_of_x.append(coord[0])
            list_of_y.append(coord[1])
    min_x = min(list_of_x)
    max_x = max(list_of_x)
    min_y = min(list_of_y)
    max_y = max(list_of_y)

    # set the grid origin
    grid_origin = (min_x, max_y)
    delta_x = (72.6685631-72.6661572)
    delta_y = (41.7575483-41.7557535)

    # set unit box to the origin
    starting_box = [grid_origin,
                    (grid_origin[0]+delta_x, grid_origin[1]),
                    (grid_origin[0]+delta_x, grid_origin[1]-delta_y),
                    (grid_origin[0], grid_origin[1]-delta_y),
                    grid_origin]

    # determine number of grids in the x and y direction.
    total_x_change = abs(max_x - min_x)  # find total x change
    number_of_x_grids = math.ceil(total_x_change/delta_x)  # divide by the shift size to find number of grids required

    total_y_change = abs(max_y - min_y)  # find total y change
    number_of_y_grids = math.ceil(total_y_change/delta_y)  # divide by the shift size to find number of grids required

    total = number_of_x_grids*number_of_y_grids

    # this box is a shapely object set at the origin point and crated using the delta x and delta y values.
    starting_box_shapely = Polygon(starting_box)

    # first x movement across the axis
    current_row_y = 0
    current_column_x = 0

    working_box = starting_box
    for i in list(range(number_of_x_grids)):
        current_column_x = current_column_x + 1
        grid.append(Polygon(working_box))
        working_box = _unit_box_move_x(starting_box, current_column_x)

    working_box = starting_box
    for i in list(range(number_of_y_grids)):
        current_column_x = 0
        current_row_y = current_row_y + 1
        y_adjusted_grid = _unit_box_move_y(starting_box, current_row_y)
        for i in list(range(number_of_x_grids)):
            grid.append(Polygon(y_adjusted_grid))
            current_column_x = current_column_x + 1
            y_adjusted_grid = _unit_box_move_y(starting_box, current_row_y)
            y_adjusted_grid = _unit_box_move_x(y_adjusted_grid, current_column_x)

    return grid


def grid_to_slippy_grid(in_polygon_coords, in_grid):

    def _deg_to_num(lon_deg, lat_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return xtile, ytile, zoom

    def _coord_lister(geom):
        return list(geom.exterior.coords)

    nesting_level = _nest_level(in_polygon_coords)
    assert nesting_level in [2, 1], "Error, input polygon cannot be read."
    if nesting_level == 2:
        feature_count = len(in_polygon_coords)
        assert feature_count == 1, f"Error, process only supports a single polygon... detected {feature_count} polygons"
        in_polygon_coords = Polygon(in_polygon_coords[0])
    elif nesting_level == 1:
        in_polygon_coords = Polygon(in_polygon_coords)
    grid_layout = pd.DataFrame(in_grid, columns=['tile'])
    df_parcels = grid_layout

    # convert testing box to slippy
    slippy_testing_box = []
    zoom = 20
    for row, column in df_parcels.iterrows():
        current_row_listed_coordinates = _coord_lister(column.tile)
        processing_list = []
        for coordinate in current_row_listed_coordinates:
            processing_list.append(_deg_to_num(coordinate[0], coordinate[1], zoom))
        slippy_testing_box.append(processing_list)

    df_parcels['slippy_grid'] = slippy_testing_box

    x_grid_size = df_parcels['slippy_grid'][1][0][0] - df_parcels['slippy_grid'][0][0][0]
    y_grid_size = None

    for row, column in df_parcels.iterrows():
        # check for the first time the y changes on the grid
        change_in_y = df_parcels.iloc[row + 1]['slippy_grid'][0][1] - df_parcels.iloc[row]['slippy_grid'][0][1]
        if change_in_y == 0:
            pass
        else:
            y_grid_size = change_in_y
            break

    intersection_geometries = []
    for row, column in df_parcels.iterrows():
        intersection_geometries.append(in_polygon_coords.intersection(column.tile))
    df_parcels['geometry'] = intersection_geometries

    df_parcels['tile_number'] = list(range(df_parcels.index.stop))

    return df_parcels


def generate_static_images(df_parcels, api_key, since=None, until=None, limit=1000, offset=0, fields=None,
                           sort="captureDate", overlap=None, include=None, exclude=None):

    from _api import polyV2
    base_url = "https://api.nearmap.com/"

    def gdal_string_cmdrun(api_key, top_left_lon_lat, bottom_right_lon_lat, output_file_name, max_res=False,
                           run_cmd=False):

        def _geom_extent(coord_list):
            x_coords = coord_list[::2]
            y_coords = coord_list[1::2]
            return f"{min(x_coords)}, {min(y_coords)}, {max(x_coords)}, {max(y_coords)}"

        from osgeo import gdal

        # flip coordinate to agree with aussies.
        #     top_left_lon_lat = top_left_lon_lat[1], top_left_lon_lat[0]
        #     bottom_right_lon_lat = bottom_right_lon_lat[1], bottom_right_lon_lat[0]

        # create a bounding box for coverage api call
        box = [top_left_lon_lat[0], top_left_lon_lat[1],
               top_left_lon_lat[0], bottom_right_lon_lat[1],
               bottom_right_lon_lat[0], top_left_lon_lat[1],
               bottom_right_lon_lat[0], bottom_right_lon_lat[1],
               top_left_lon_lat[0], top_left_lon_lat[1]]

        # convert bounding box to extent format
        box = _geom_extent(box)

        '''This will return a json of the coverage in the AOI'''

        # Set Resolution as HC2 max res
        coverage_json = polyV2(base_url, api_key, box, since, until, limit, offset, fields, sort, overlap, include,
                               exclude)
        print(coverage_json)
        df = pd.DataFrame(data=coverage_json['surveys'])
        df.sort_values(by=['captureDate'], ascending=False, inplace=True)
        resolution = df.head(1)['pixelSize'].values[0]

        if max_res:
            resolution = resolution
        else:
            resolution = .40
        print('Resolution is: ' + str(resolution))

        '''First Bounding Box Coordinate, TOP LEFT'''
        top_left = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), top_left_lon_lat[0], top_left_lon_lat[1])
        # print(transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), -72.672874, 41.759577))  # longitude first, latitude second.
        # output (meters east of 0, meters north of 0): (-8089907.32816373, 5125033.0039063785)
        '''Second Bounding Box Coordinate, BOTTOM RIGHT'''
        bottom_right = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), bottom_right_lon_lat[0],
                                 bottom_right_lon_lat[1])
        # print(transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), -72.658641, 41.751525))  # longitude first, latitude second.
        # output (meters east of 0, meters north of 0): (-8089907.32816373, 5125033.0039063785)

        long_difference = bottom_right[0] - top_left[0]
        lat_difference = bottom_right[1] - top_left[1]
        long_pixel_count = abs(long_difference / resolution)
        lat_pixel_count = abs(lat_difference / resolution)

        #################

        #     print('gdal_translate --debug ON  -a_srs EPSG:3857 -projwin ' + tuple_to_string(top_left_lon_lat) + tuple_to_string(bottom_right_lon_lat) + '-projwin_srs "EPSG:4326" -outsize ' + str(long_pixel_count) + ' ' +str(lat_pixel_count) + ' tile_dl_blank.xml coltgateway.tif')

        print(top_left_lon_lat)

        '''
        top_left = tuple_to_string(top_left_lon_lat)
        bottom_right = tuple_to_string(bottom_right_lon_lat)
        output_file_name = output_file_name
        gdal_string = f'gdal_translate --debug ON -a_srs EPSG:3857 -projwin {top_left}{bottom_right}-projwin_srs "EPSG:4326" -outsize {long_pixel_count} {lat_pixel_count} tile_dl.xml {output_file_name}'
        #     os.chdir(temp_dir)
        #     os.getcwd()
        if run_cmd == True:
            print(getcwd())
            print(gdal_string)
            print(f'{temp_dir}')
            run(gdal_string, shell=True)
        else:
            print(gdal_string)
        #TODO: replace the above with python gdal translate https://gis.stackexchange.com/questions/352643/gdal-translate-in-python-where-do-i-find-how-to-convert-the-command-line-argum
        '''

    for row, column in df_parcels.iterrows():
        if not column.geometry.is_empty:
            top_left_lon_lat = list(df_parcels.tile[row].exterior.coords[0])
            bottom_right_lon_lat = list(df_parcels.tile[row].exterior.coords[2])
            static_image_name = f'static_image_cell_number_{row}.tif'
            print(top_left_lon_lat, bottom_right_lon_lat, static_image_name)

            gdal_string_cmdrun(api_key, top_left_lon_lat, bottom_right_lon_lat, static_image_name, max_res=False,
                               run_cmd=True)  # create image