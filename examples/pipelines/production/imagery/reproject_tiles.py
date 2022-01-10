from pathlib import Path
import geopandas as gpd
from os.path import split, splitext, basename
from shutil import rmtree
import concurrent.futures
from os import cpu_count
from tqdm import tqdm
from shapely.geometry import mapping, Polygon
import fiona
from osgeo import gdal
import time
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)


def _create_folder(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def shapely_polygon_to_shp(in_shapely_geom, crs, out_shapefile):

    # Define a polygon feature geometry with one attribute
    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int'},
    }

    # Write a new Shapefile
    with fiona.open(out_shapefile, 'w', crs=crs, driver='ESRI Shapefile', schema=schema) as c:
        c.write({
            'geometry': mapping(in_shapely_geom),
            'properties': {'id': 1},
        })
    return out_shapefile


def get_file_crs(in_file):
    with fiona.open(in_file, mode="r") as source:
        crs = source.crs.get('init').upper()
        return crs


def get_db_layer_crs(in_db, layer):
    with fiona.open(in_db, layer=layer.replace("main.", ""), mode="r") as source:
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


def delete_shapefile(in_shapefile):
    in_shp = Path(in_shapefile)
    shp_fmts = ['.shp', '.shx', '.dbf', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.atx', '.ixs', '.mxs', '.prj',
                '.xml', '.cpg']
    [in_shp.with_suffix(_).unlink() for _ in shp_fmts if in_shp.with_suffix(_).is_file()]


def reproject_image(input_vrt, scratch_dir, output_image, output_image_format, output_crs, mask_geometry,
                    bounds_geometry=None, resample_alg='bilinear'):
    scratch_dir = Path(scratch_dir)
    output_image = Path(output_image).as_posix()
    input_vrt = Path(input_vrt).as_posix()

    formats = {'tif': {'gdal_name': 'GTiff', 'opacity_supported': True, 'compression_supported': True},
               'tiff': {'gdal_name': 'GTiff', 'opacity_supported': True, 'compression_supported': True},
               'jpg': {'gdal_name': 'JPG', 'opacity_supported': False, 'compression_supported': False},
               'png': {'gdal_name': 'PNG', 'opacity_supported': True, 'compression_supported': False}
               }
    opacity_supported = formats.get(output_image_format).get('opacity_supported')
    #try:
    output_bounds = None
    output_bounds_srs = None
    mask_shapefile = None
    crop_to_cutline = False
    if bounds_geometry is not None:
        output_bounds_srs = output_crs
        if type(bounds_geometry).__name__ == "GeoDataFrame":
            output_bounds = bounds_geometry.total_bounds
        elif type(bounds_geometry).__name__ == "Polygon":
            output_bounds = bounds_geometry.bounds
        else:
            print(f"Error: Geometry type for 'mask_geometry' {type(mask_geometry)} is not supported")
    # TODO: If Bounds Geometry clip mask geometry to bounds before saving as .shp
    if mask_geometry is not None:
        mask_shapefile = (scratch_dir / f"{splitext(basename(output_image))[0]}.shp")
        crop_to_cutline = True
        if type(mask_geometry).__name__ == "GeoDataFrame":
            write_gdf_to_file(gdf=mask_geometry, output_file=mask_shapefile)
        elif type(mask_geometry).__name__ == "Polygon":
            shapely_polygon_to_shp(mask_geometry, output_crs, mask_shapefile)
        else:
            print(f"Error: Geometry type for 'mask_geometry' {type(mask_geometry)} not supported")

    warp_options = gdal.WarpOptions(format=formats.get(output_image_format).get('gdal_name'),
                                    resampleAlg=resample_alg,
                                    dstSRS=output_crs,
                                    outputBounds=output_bounds,
                                    outputBoundsSRS=output_bounds_srs,
                                    cutlineDSName=mask_shapefile,
                                    cropToCutline=crop_to_cutline,
                                    dstAlpha=opacity_supported)

    gdal.Warp(output_image, input_vrt, options=warp_options)
    if type(mask_geometry).__name__ == "GeoDataFrame":
        del mask_geometry
    if mask_shapefile is not None:
        if Path(mask_shapefile).is_file():
            delete_shapefile(in_shapefile=mask_shapefile)
    '''
    except Exception as e:
        print(f'VRT to image file conversion failed for {output_image} | {e}')
    '''
    # TODO Return Geometry of output Tile, Tile ID, and Tile Name to merge in the results manifest geojson
    temp = dict()
    temp['tile'] = output_image
    return temp


def reprojection(input_dir, output_dir, tile_manifest=None, mask_geometry=None, output_crs:str=None,
                 max_cores:int=None):
    """
    The following function is used to take the output from the production code, "get_tiles_production_mapping.py". Once
    the imagery download is pulled for a specific size tiling structure, this script is used to run on the subsequent
    imagery tiles, convert to a virtual raster tileset, reproject, and then convert back to a geotiff for use in the
    converted coordinate system.

    Note: This is a working codebase, Python Bindings need to be added.
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    assert type(output_crs).__name__ == "str", "Error: 'output_crs' is not a string"
    output_crs = output_crs.upper()
    supported_epsg_prefixes = ["ESRI:", "EPSG:"]
    assert output_crs.startswith(tuple(supported_epsg_prefixes)), f"Error: 'output_crs' {output_crs} not a member of " \
                                                                  f"{supported_epsg_prefixes}"
    # TODO: Add assertions to ensure CRS is a legit CRS (EPSG, ESRI...) and not WGS84
    assert input_dir.is_dir, f"Error: 'input_dir' must be a directory... {input_dir} is not supported"
    assert not output_dir.is_file(), f"Error: 'output_dir' {output_dir} cannot be a file... must be a folder/directory"
    supported_vector_formats = [".shp", ".geojson"]
    # TODO: Add assertion support for geopackage layer as input
    for _ in [["tile_manifest", tile_manifest], ["mask_geometry", mask_geometry]]:
        if _[1] is not None:
            _[1] = Path(_[1])
            assert _[1].is_file(), f"Error: '{_[0]}' {_[1]} must be a file."
            assert _[1].suffix in supported_vector_formats, f"Error: '{_[0]}' {_[1]} not a member of " \
                                                            f"{supported_vector_formats}"

    print('User Input Values:')
    print('=' * 30)
    print(f'Imagery in the following File Path is being Processed: {input_dir}')
    print(f'Processed Files will be saved to the following Location: {output_dir}')
    print(f'Imagery is being Projected from WGS84 to the following Spatial Reference Code: {output_crs}')
    print('_' * 30)
    start_time = time.perf_counter()

    supported_raster_formats = [".jpg", ".tif"]
    source_image_list = [_.as_posix() for _ in list(Path(input_dir).iterdir()) if _.suffix in supported_raster_formats]
    print(f'Detected {len(source_image_list)} Images for processing')
    assert len(source_image_list) > 0, f"Error: No supported images detected in {input_dir} that are members of " \
                                       f"{supported_raster_formats}"

    _create_folder(output_dir)
    tile_manifest_gdf = None
    if tile_manifest:
        crs = get_file_crs(tile_manifest)
        if crs == output_crs:
            to_crs = None
        else:
            print(f"Reprojecting 'tile_manifest' CRS from {crs} to 'output_crs' {output_crs}")
            to_crs = output_crs
        tile_manifest_gdf = read_file_as_gdf(tile_manifest, mask=None, to_crs=to_crs)
    mask_geometry_gdf = None
    if mask_geometry:
        crs = get_file_crs(mask_geometry)
        if crs == output_crs:
            to_crs = None
        else:
            print(f"Reprojecting 'mask_geometry' CRS from {crs} to 'output_crs' {output_crs}")
            to_crs = output_crs
        mask_geometry_gdf = read_file_as_gdf(mask_geometry, mask=None, to_crs=to_crs)


    print(f'creating a vrt for the images in the processing folder...')
    sample_image = source_image_list[0]
    input_image_format = Path(sample_image).suffix.strip(".")
    vrt_options = None
    rds = gdal.Open(sample_image)  # Sample first image to detect if alpha band (band-4) already exists
    if rds.RasterCount > 3:
        if input_image_format == "jpg":
            vrt_options = gdal.BuildVRTOptions(addAlpha=False) #resampleAlg=None
        elif input_image_format == "tif":
            vrt_options = gdal.BuildVRTOptions(addAlpha=False)
    else:
        if input_image_format == "jpg":
            vrt_options = gdal.BuildVRTOptions(addAlpha=False)  # resampleAlg=None
        elif input_image_format == "tif":
            vrt_options = gdal.BuildVRTOptions(addAlpha=True)
    rds = None  # Destroys the Open GDAL Operation
    vrt_file = (output_dir / "original_virtual_file.vrt").as_posix()
    my_vrt = gdal.BuildVRT(vrt_file, source_image_list, options=vrt_options)
    my_vrt = None  # Destroys the VRT Opertion to remove the shapefile lock. Necessary for concurrent processing

    scratch_dir = output_dir / "scratch"
    _create_folder(scratch_dir)

    processed_tiles = []

    if tile_manifest is None:
        output_image = output_dir / f"tile.{input_image_format}"
        reproject_image(input_vrt=vrt_file,
                        scratch_dir=scratch_dir,
                        output_image=output_image,
                        output_image_format=input_image_format,
                        output_crs=output_crs,
                        mask_geometry=mask_geometry_gdf)

    elif tile_manifest:

        # TODO: Implement Multiprocessing here MFA's
        print("Commence Imagery Reprojection & Tiline Process")
        system_cores = cpu_count()
        if max_cores:
            if max_cores > system_cores:
                print(f"User Input {max_cores} 'max_cores' > system cpu cores. Reverting to {system_cores} 'max_cores'")
                max_cores = system_cores
            elif max_cores < system_cores:
                print(
                    f"User Input {max_cores} 'max_cores' < {system_cores} available system cpu cores... continuing process")
        else:
            max_cores = system_cores
        num_features = None
        if type(tile_manifest_gdf).__name__ == "GeoDataFrame":
            num_features = len(tile_manifest_gdf.index)
        num_cores = None
        if num_features > max_cores:
            num_cores = max_cores

        with concurrent.futures.ProcessPoolExecutor(num_cores) as executor:
            with tqdm(total=num_features) as progress:
                jobs = []
                for index, row in tile_manifest_gdf.iterrows():
                    geometry = tile_manifest_gdf.loc[index, 'geometry']
                    output_image = output_dir / f"tile_{index}.{input_image_format}"
                    jobs.append(executor.submit(reproject_image,
                                                input_vrt=vrt_file,
                                                scratch_dir=scratch_dir.as_posix(),
                                                output_image=output_image.as_posix(),
                                                output_image_format=input_image_format,
                                                output_crs=output_crs,
                                                bounds_geometry=geometry,
                                                mask_geometry=mask_geometry_gdf))
                for job in jobs:
                    result = job.result()
                    #if result is not None:
                    #    processed_tiles.extend(result)
                    progress.update()
    #print(len(processed_tiles))
    #print(processed_tiles)
    # Cleaup After Processing
    rmtree(scratch_dir, ignore_errors=True)
    del my_vrt
    Path(vrt_file).unlink()

    # TODO Create VRT File of resulting data
    # TODO: Create GeoJSON Manifest of resulting data

    end_time = time.perf_counter()
    total_time = end_time-start_time
    total_min = total_time/60
    print(f'processing time is: {total_time}')
    print(f'processing time in minutes is: {total_min}')


if __name__ == "__main__":

    ###############
    # User Inputs
    #############

    input_dir = r'C:/output_tiles/FL/1245025_MiamiBeach'
    output_dir = r'C:/output_test'
    tile_manifest = r'C:/output_tiles/FL/1245025_MiamiBeach/manifest_extents.geojson'
    output_crs = 'EPSG:2236'  # Example: NAD83 Florida East (ftUS) | Lookup your CRS at: http://www.spatialreference.org

    reprojection(input_dir, output_dir, tile_manifest, output_crs=output_crs)
