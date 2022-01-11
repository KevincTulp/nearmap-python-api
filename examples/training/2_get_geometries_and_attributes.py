from nearmap.geospatial.fileio import read_file_as_gdf

in_file = r'../pipelines/production/test_data/parcels_with_pools.geojson'

file_df = read_file_as_gdf(in_file)

columns = file_df.columns
print(f"Detected Dataframe Columns as: {columns}")

for index, row in file_df.iterrows():
    # [print(f"{_} =", row.get(_)) for _ in columns]
    print(index, row.get('property_id'), row.get('geometry'))

