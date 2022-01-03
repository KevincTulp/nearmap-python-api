from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path
from math import degrees, radians, atan, sinh, tan, pi, log, cos

try:
    from ujson import dump, dumps, loads
except ModuleNotFoundError:
    from json import dump, dumps, loads


def latlon_to_xy(lat, lon, z):
    def sec(x):
        return 1 / cos(x)
    tile_count = pow(2, z)
    xtile = (lon + 180) / 360
    ytile = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return int(tile_count*xtile), int(tile_count*ytile)


def xy_to_latlon(xtile, ytile, z):
    n = pow(2, z)
    lon_deg = (xtile / n * 360.0) - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return lat_deg, lon_deg


def get_geometry_extent(in_coord_list):
    x_coords = in_coord_list[::2]
    y_coords = in_coord_list[1::2]
    x_min = sorted(x_coords)[0]
    x_max = sorted(x_coords)[-1]
    y_min = sorted(y_coords)[0]
    y_max = sorted(y_coords)[-1]
    return [x_min, y_min, x_max, y_max]


def get_extent_centroid(in_extent_coords):
    x_min = in_extent_coords[0]
    x_max = in_extent_coords[2]
    y_min = in_extent_coords[1]
    y_max = in_extent_coords[3]
    x = x_min + ((x_max - x_min) / 2)
    y = y_min + ((y_max - y_min) / 2)
    return [x, y]


def get_parcel_geoms_and_attributes(parcel_geojson):
    f = open(parcel_geojson, "r")
    my_json = loads(f.read())
    json_properties_keys = list([p.keys() for p in [i["properties"] for i in my_json["features"]]][0])
    print(f"Available json attributes are: {json_properties_keys}")

    parcel_data = [[i["properties"]["LocAddr"],
                    i["properties"]["city"],
                    i["properties"]["zip"],
                    [item for sublist in i['geometry']['coordinates'][0] for item in sublist],]
                   for i in my_json["features"]]
    f.close()
    print(f"Detected {len(parcel_data)} Parcels in parcel_data for processing")
    return parcel_data


def download_ai_packs_and_imagery():
    parcel_data = get_parcel_geoms_and_attributes(parcel_geojson)

    # query available ai packs
    my_packs = nearmap.aiPacksV4()
    available_packs = [i['code'] for i in my_packs["packs"]]
    print(f"AI Packs I have access: {available_packs}")

    print(f"Downloading data for {len(parcel_data)} parcels")
    tile_directions = ["Vert", "North", "South", "East", "West"]
    count = 0
    for p in parcel_data:
        loc_addr = p[0]
        city = p[1]
        zip = p[2]
        geom = p[3]
        folder = f"{out_directory}\\{loc_addr.replace(' ', '_')}__{city}__{zip}"
        Path(folder).mkdir(parents=True, exist_ok=True)
        # Download AI Packs
        if packs:
            if packs == "All_Individual":
                for pack in available_packs:
                    my_ai_features = nearmap.aiFeaturesV4(geom, since, until, pack, out_format="json",
                                                          lat_lon_direction="yx")
                    with open(f'{folder}\\{pack}.json', 'w', encoding='utf-8') as f:
                        dump(my_ai_features, f, ensure_ascii=False, indent=4)
            else:
                my_ai_features = nearmap.aiFeaturesV4(geom, since, until, packs, out_format="json",
                                                      lat_lon_direction="yx")
                with open(f'{folder}\\{packs}.json', 'w', encoding='utf-8') as f:
                    dump(my_ai_features, f, ensure_ascii=False, indent=4)
        if not packs:
            my_ai_features = nearmap.aiFeaturesV4(geom, since, until, packs, out_format="json", lat_lon_direction="yx")
            with open(f'{folder}\\all_packs.json', 'w', encoding='utf-8') as f:
                dump(my_ai_features, f, ensure_ascii=False, indent=4)
        # Download Imagery
        image_folder = f"{folder}\\Images"
        Path(image_folder).mkdir(parents=True, exist_ok=True)
        for tile_direction in tile_directions:
            wgs84_x, wgs84_y = get_extent_centroid(get_geometry_extent(geom))
            slippy_y, slippy_x = latlon_to_xy(lat=wgs84_y, lon=wgs84_x, z=z_level)
            out_image = f"{image_folder}\\{tile_direction}.{image_format}"
            image_tile_file = nearmap.tileV3(tile_direction, z_level, slippy_y, slippy_x, image_format, out_image)
    count += 1


if __name__ == "__main__":
    # Connect to the Nearmap API for Python
    # nearmap = NEARMAP("My_API_Key_Goes_Here")  # Paste or type your API Key here as a string
    nearmap = NEARMAP(get_api_key())
    print(f"My API Key Is: {nearmap.api_key}")

    ###################
    # User Parameters
    #################

    # parcel_geojson = r'C:\Parcels_geojson.json'
    root = str(Path(__file__).parents[2]).replace('\\', '/')  # Get root of project
    parcel_geojson = f"{root}/nearmap/unit_tests/TestData/Parcels_Vector/JSON/Parcels_geojson.json"
    out_directory = r'ai_packs_sample'

    # AI API Settings
    since = None  # Since Data ex: "2018-08-01"
    until = None  # Until Date ex: "2021-07-09"
    packs = "All_Individual"  # None  # Set to None for all packs otherwise type pack of interest name(s)

    # Tile API Settings
    z_level = 19
    image_format = "jpg"

    ##########
    # Script
    ########

    download_ai_packs_and_imagery()
