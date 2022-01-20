from pathlib import Path
from coverage_assessment import detect_coverage
from tqdm import tqdm
import os


def bulk_detect_coverage(api_key, input_dir, output_dir):
    input_dir = Path(input_dir)
    assert input_dir.is_dir(), f"Error: {input_dir} is not a directory"
    supported_formats = [".geojson", ".shp"]  # TODO: Add Support for geopackage
    files = [_ for _ in input_dir.rglob('*') if _.suffix in supported_formats]
    with tqdm(total=len(files)) as bulk_progress:
        for file in files:
            output_folder = Path(output_dir) / file.parents[0].as_posix().strip(f'{input_dir.as_posix()}')
            extension = file.suffix.strip('.')
            try:
                detect_coverage(api_key, file, output_folder, out_file_extension="geojson")
            except ValueError as e:
                print(f"Error: processing {file} | {e}")
            except Exception as e:
                print(f"Error: processing {file} | {e}")
            bulk_progress.update()


if __name__ == "__main__":
    input_dir = r'C://Australia'
    output_dir = r'C://Australia_Processed'
    api_key = os.environ.get("NEARMAP_API_KEY")
    bulk_detect_coverage(api_key, input_dir, output_dir)
