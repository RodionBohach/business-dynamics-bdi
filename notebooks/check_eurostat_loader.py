# %%
from pathlib import Path
import sys

project_root = Path.cwd().parent
sys.path.insert(0, str(project_root / "src"))

from data.load_eurostat import load_eurostat_data
# %%
raw_path = project_root / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"
historical_demography = load_eurostat_data(str(raw_path))
# %%
economic_accounts_path = project_root / "data/raw/nama_10_a64_Gross_value_added_and_income.tsv.gz"
economic_accounts = load_eurostat_data(str(economic_accounts_path))
# %%
