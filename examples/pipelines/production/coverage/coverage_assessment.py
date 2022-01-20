from nearmap.geospatial.fileio import read_file_as_gdf, write_gdf_to_file
from nearmap import NEARMAP
from pathlib import Path
from shapely.geometry import Polygon
import geopandas as gpd
from shutil import rmtree
from tqdm import tqdm
import os
try:
    from ujson import dump, dumps
except ModuleNotFoundError:
    from json import dump, dumps
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)


def gdf_mask(in_gdf, crs='epsg:4326'):
    xmin, ymin, xmax, ymax = in_gdf.total_bounds
    polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])
    out_gdf = gpd.GeoDataFrame()
    out_gdf.loc[0, 'geometry'] = polygon
    return out_gdf.set_crs(crs=crs)


def main(api_key, input_file, output_folder, out_file_extension="geojson"):

    read_file_gdf = read_file_as_gdf(input_file)
    file_gdf = read_file_gdf.to_crs(3857)
    del read_file_gdf

    file_df_type = file_gdf.geom_type[0]
    supported_geoms = ["MultiPolygon", "Polygon"]
    assert file_df_type in supported_geoms, f"input_file geometry not a member of {supported_geoms}"
    if file_df_type == "MultiPolygon":
        file_df = file_gdf.explode(index_parts=False)

    out_folder = Path(output_folder)
    scratch_folder = out_folder / "scratch"
    scratch_folder.mkdir(parents=True, exist_ok=True)

    nearmap = NEARMAP(api_key)
    coverage = nearmap.coverageV2()
    coverage_geojson = scratch_folder / 'coverage.geojson'
    if coverage_geojson.is_file():
        coverage_geojson.unlink()
    with open(coverage_geojson, 'w', encoding='utf-8') as f:
        dump(coverage, f, ensure_ascii=False, indent=4)

    read_coverage_df = gpd.read_file(coverage_geojson)
    coverage_gdf = read_coverage_df.to_crs(3857)
    del read_coverage_df

    with tqdm(total=len(coverage_gdf.index)) as progress:
        for index, row in coverage_gdf.iterrows():
            data_type = row.get('type')
            progress.set_description(f"Processing {data_type}")
            coverage_gdf_subset = gpd.GeoDataFrame(geometry=gpd.GeoSeries(row.get('geometry')), crs=3857)
            try:
                intersect_geom = file_gdf.intersection(coverage_gdf_subset).explode(index_parts=False)
            except AttributeError as e:
                print(e)
                intersect_geom = file_gdf.intersection(coverage_gdf_subset)
            intersect_geom = intersect_geom[~intersect_geom.is_empty]
            result_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(intersect_geom))
            result_gdf['area_sq_meter'] = result_gdf.area
            result_gdf['area_sq_km'] = result_gdf.area / 10**6
            output_file = out_folder / f"coverage_{data_type}.{out_file_extension}"
            write_gdf_to_file(result_gdf.to_crs(4326), output_file)
            rmtree(scratch_folder, ignore_errors=True)
            del coverage_gdf_subset, intersect_geom, result_gdf
            progress.update()
        progress.set_description(f"Process Complete")


if __name__ == "__main__":
    input_file = r''
    output_folder = r''
    out_file_extension = "geojson"  # Options: "shp", "geojson", "geopackage/layer"
    api_key = os.environ.get("NEARMAP_API_KEY")
    main(api_key, input_file, output_folder, out_file_extension)
