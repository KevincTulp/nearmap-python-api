from nearmap.geospatial.fileio import read_file_as_gdf
from nearmap import NEARMAP
from nearmap.auth import get_api_key
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

nearmap = NEARMAP(get_api_key())

in_file = Path('../pipelines/production/test_data/parcels_with_pools.geojson')
property_id = ''
since = None
until = None
packs = None
out_format = "shp"
out_folder = Path('parcels')

out_folder.mkdir(parents=True, exist_ok=True)

file_df = read_file_as_gdf(in_file)


def get_polygon(in_geometry):
    get_polygon = [[float(_[0]), float(_[1])] for _ in list(in_geometry.exterior.coords)]
    return [item for sublist in get_polygon for item in sublist]

num_features = len(file_df.index)
print(f"Begin Downloading {num_features} AI features")
with tqdm(total=num_features) as progress:
    for index, row in file_df.iterrows():
        output = out_folder / row.get('property_id')
        polygon = get_polygon(row['geometry'])
        nearmap.aiFeaturesV4(polygon, since, until, packs, out_format, output, lat_lon_direction="yx")
        progress.update()
