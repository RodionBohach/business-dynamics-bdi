# %%
from pathlib import Path
import hashlib
import pandas as pd
project_root = Path(__file__).resolve().parents[1]
raw_dir = project_root / 'data/raw'
raw_files = sorted(raw_dir.glob('*.tsv.gz'))
import json
# %%
raw_path = raw_files[0]

raw_table = pd.read_csv(raw_path, sep='\t', compression='gzip', dtype=str, keep_default_na=False)
# %%
first_column_name = raw_table.columns[0]
dimension_names = first_column_name.split('\\')[0].split(',')
# %%
raw_dimensions = raw_table.iloc[:, 0].str.split(",", expand=True)
raw_dimensions.columns = dimension_names
# %%
geographies = sorted(raw_dimensions["geo"].unique())
# %%
dimension_values = {}

for dimension in dimension_names: dimension_values[dimension] = sorted(raw_dimensions[dimension].unique())
# %%
years = raw_table.columns[1:].str.strip().tolist()
# %%
file_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
# %%
source_record = {
    'filename': raw_path.name,
    'download_date': '2026-10-08',
    'sha256': file_sha256,
    'raw_rows': raw_table.shape[0],
    'years': years,
    'dimensions': dimension_values,
}
# %%
source_records = []

for raw_path in raw_files: 
    raw_table = pd.read_csv(raw_path, sep='\t', compression='gzip', dtype=str, keep_default_na=False)

    first_column_name = raw_table.columns[0]
    dimension_names = first_column_name.split('\\')[0].split(',')
    raw_dimensions = raw_table.iloc[:, 0].str.split(",", expand=True)
    raw_dimensions.columns = dimension_names
    

    dimension_values = {}

    for dimension in dimension_names:
        dimension_values[dimension] = sorted(
            raw_dimensions[dimension].unique()
        )
    years = raw_table.columns[1:].str.strip().tolist()

    file_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    source_record = {
    'filename': raw_path.name,
    'download_date': '2026-10-08',
    'sha256': file_sha256,
    'raw_rows': raw_table.shape[0],
    'years': years,
    'dimensions': dimension_values,

    }
    source_records.append(source_record)
# %%
manifest_path = project_root / "docs/raw_sources_manifest.json"

manifest_path.write_text(
    json.dumps(source_records, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
# %%
