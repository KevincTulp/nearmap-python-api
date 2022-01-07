####################################
#   File name: Join_AI_To_Parcel_Dataset.py
#   About: Process for detecting parcels that contain AI data. Requires parcel dataset to query
#   Authors: Geoff Taylor | Sr Solution Architect | Nearmap
#   Date created: 1/07/2022
#   Last update: 1/07/2022
#   Python Version: 3.8+
####################################

from pathlib import Path
import geopandas as gpd
import fiona
from os.path import split, splitext


def get_file_crs(in_file):
    with fiona.open(in_file, "r") as source:
        crs = source.crs.get('init').upper()
        return crs


def get_db_layer_crs(in_db, layer):
    with fiona.open(in_db, layer=layer.replace("main.", "")) as source:
        crs = source.crs.get('init').upper()
        return crs


def read_file_as_gdf(in_file, mask=None, to_crs='EPSG:4326'):
    supported_formats = [".shp", ".geojson"]
    supported_gdbs = [".gpkg", ".gdb"]
    f = Path(in_file)
    if f.is_dir():
        print(f"Detected input {in_file} as a Directory. Input must be a file or geodatabase/feature")
        exit()
    elif f.is_file():
        assert f.is_file(), f"Error: File {in_file} does not exist"
        assert f.suffix in supported_formats, f"Error: {in_file} format not a member of {supported_formats}"
        file_crs = get_file_crs(in_file)
        if file_crs is None or file_crs == to_crs:
            return gpd.read_file(f, mask=mask)
        else:
            return gpd.read_file(f, mask=mask).to_crs(to_crs)
    elif f.parents[0].suffix in supported_gdbs:
        gdb_name = f.parents[0]
        gdb_type = gdb_name.suffix
        layer_name = f.name
        get_db_layer_crs(gdb_name, layer_name)
        if gdb_type == ".gpkg":
            layer_name = layer_name.replace("main.", "")
            layer_crs = get_db_layer_crs(gdb_name, layer_name)
            if layer_crs is None or layer_crs == to_crs:
                return gpd.read_file(gdb_name, layer=layer_name, mask=mask)
            else:
                return gpd.read_file(gdb_name, layer=layer_name, mask=mask).to_crs(to_crs)
        elif gdb_type == ".gdb":
            print("Error: Esri GeoDatabase Format Not Supported")
            exit()
    else:
        print(f"Unable to detect file format for {in_file} or file format not supported")


def write_gdf_to_file(gdf=None, output_file=None):
    output_file = Path(output_file).resolve().as_posix()
    print(output_file)
    supported_formats = [".shp", ".geojson"]
    supported_gdbs = [".gpkg", ".gdb"]
    if splitext(output_file)[1] in supported_formats:
        if output_file.endswith(".geojson"):
            return gdf.to_file(output_file, driver='GeoJSON')
        elif output_file.endswith(".shp"):
            return gdf.to_file(output_file)
    elif splitext(output_file)[1] in supported_gdbs:
        if output_file.endswith(".gpkg"):
            return gdf.to_file(output_file, layer="feature")
        elif output_file.endswith(".gdb"):
            print("Error: Esri GeoDatabase Format Not Supported")
            exit()
    elif splitext(split(output_file)[0])[1] in supported_gdbs:
        db, layer = split(output_file)
        db_format = splitext(db)[1]
        if db_format == ".gpkx":
            return gdf.to_file(Path(output_file), layer=layer)
        elif db_format == ".gdb":
            print("Error: Esri GeoDatabase Format Not Supported")
            exit()
    else:
        print(f"Error: Could not detect file format for {output_file} or format not supported")
        exit()


def create_image_download_manifest(input_ai_dataset, input_parcel_dataset, output_file, input_processing_bounds=None):
    mask = None
    if input_processing_bounds:
        mask = read_file_as_gdf(input_processing_bounds, to_crs='EPSG:4326')
        if len(mask.index) > 1:
            dissolve_col_name = 'dissolve_column'
            mask[dissolve_col_name] = 0
            mask = mask.dissolve(by=dissolve_col_name)
        print(f"Detected {len(mask.index)} Features in Mask dataset")
    if mask is not None:
        ai_dataset = read_file_as_gdf(input_ai_dataset, to_crs='EPSG:4326')
        print(f"Detected {len(ai_dataset.index)} Features in source AI dataset")
        parcel_dataset_source = read_file_as_gdf(input_parcel_dataset, to_crs='EPSG:4326')
        print(f"Detected {len(parcel_dataset_source.index)} Features in source Parcel dataset")
        parcel_dataset = gpd.clip(parcel_dataset_source, mask)
        print(f"Detected {len(parcel_dataset.index)} Features in masked Parcel dataset")
        del parcel_dataset_source
    else:
        ai_dataset = read_file_as_gdf(input_ai_dataset, to_crs='EPSG:4326')
        print(f"Detected {len(ai_dataset.index)} Features in source AI dataset")
        parcel_dataset = read_file_as_gdf(input_parcel_dataset, to_crs='EPSG:4326')
        print(f"Detected {len(parcel_dataset.index)} Features in source Parcel dataset")
    join_df = parcel_dataset.sjoin(ai_dataset, how="inner")
    print(f"Detected {len(join_df.index)} Parcels containing AI detected Features")
    del ai_dataset, parcel_dataset
    if mask is not None:
        del mask
    print(f"Outputting Results to {output_file}")
    return write_gdf_to_file(join_df, output_file)


if __name__ == "__main__":

    ###################
    # User Parameters
    #################

    input_ai_dataset = r'data/Swimming_Pool.gpkg/main.Swimming_Pool'
    input_processing_bounds = r'data/processing_bounds/NEW_ZONE_FINALS_2022.shp'
    input_parcel_dataset = r'data/parcels/Parcel_Polygons.shp'
    output_file = r'data/output/parcels_to_process1.geojson'

    ##########
    # Script
    ########
    create_image_download_manifest(input_ai_dataset, input_parcel_dataset, output_file, input_processing_bounds)
