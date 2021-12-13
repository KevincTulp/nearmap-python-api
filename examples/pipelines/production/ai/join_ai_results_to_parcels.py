from pathlib import Path
import geopandas as gpd
import pandas as pd
from tqdm.auto import tqdm


def _create_folder(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_associated_files(parcel_dir, processed_dir):
    """ Obtain a dictionary of appropriately grouped files for QA/QC process"""
    parcel_files = list(Path(parcel_dir).iterdir())
    processed_files = list(Path(processed_dir).iterdir())
    d = dict()
    id = 0
    for p in parcel_files:
        nd = dict()
        nd["parcel"] = p
        for r in processed_files:
            if p.stem in r.stem:
                if "errors" in r.stem:
                    nd["errors"] = r
                elif "features" in r.stem and r.suffix == ".geojson":
                    nd["geojson"] = r
                elif p.stem == r.stem:
                    nd["success"] = r
        d[id] = nd
        id +=1
    return d

def attribute_parcels(project_dir, unique_fid, features_of_interest):

    parcel_dir = f"{project_dir}\parcels"
    processed_dir = f"{project_dir}\processed"
    files = get_associated_files(parcel_dir, processed_dir)

    for f in tqdm(files):

        parcel_file = files[f].get('parcel')
        out_file_basename = parcel_file.stem
        success_file = files[f].get('success')

        parcel_gdf = gpd.read_file(parcel_file)

        features = [f'{f}_present' for f in features_of_interest]
        cols = features.copy()
        cols.append(unique_fid)
        success_file_df = pd.read_csv(success_file, usecols=cols)
        #print(success_file_df.columns)
        #print(success_file_df.head())

        #parcelz_gdf = gpd.GeoDataFrame(parcel_gdf.merge(success_file_df, on=unique_fid).drop_duplicates())
        parcelz_gdf = gpd.GeoDataFrame(parcel_gdf.merge(success_file_df, on=unique_fid))
                                       #.drop_duplicates(subset=[unique_fid, 'geometry_y']).rename(columns={"geometry_x": "geometry"}))
        #print(parcelz_gdf.columns)
        #print(parcelz_gdf.head())

        del success_file_df
        out_dir = f'{project_dir}\\parcels_with_ai'
        _create_folder(out_dir)

        if len(features) > 1:
            query_str = ''.join([f"{i}!='N' or " for i in features[:-1]] + [f"{features[-1]}!='N'"])
        else:
            query_str = f"{features[0]}!='N'"
        includes_gdf = parcelz_gdf.query(query_str)
        includes_gdf.to_file(f"{out_dir}\\{out_file_basename}_includes.geojson", driver='GeoJSON')
        del includes_gdf

        if len(features) > 1:
            query_str = ''.join([f"{i}=='N' or " for i in features[:-1]] + f"{features[-1]}=='N'")
        else:
            query_str = f"{features[0]}=='N'"
        excludes_gdf = parcelz_gdf.query(query_str)
        excludes_gdf.to_file(f"{out_dir}\\{out_file_basename}_excludes.geojson", driver='GeoJSON')
        del excludes_gdf, parcelz_gdf, parcel_gdf


if __name__ == "__main__":

    project_dir = r'C:\Users\geoff.taylor\Dropbox (Nearmap)\Insurance\Farmers\pools_project'
    unique_fid = 'parcel_id'
    features_of_interest = ['swimming_pool']

    # Resulting GeoJSON data will be output to a folder within 'project_dir' called 'parcels_with_ai'

    attribute_parcels(project_dir, unique_fid, features_of_interest)