from nearmap.geospatial.fileio import read_file_as_gdf

in_file = r'../pipelines/production/test_data/parcels_with_pools.geojson'

file_df = read_file_as_gdf(in_file)
print(file_df.head(5))


for index, row in file_df.iterrows():
    print(f"On Item {index} | {row}")
