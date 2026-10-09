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
historical_high_growth_raw = project_root / "data/raw/bd_9pm_r2_High_growth_enterprises.tsv.gz"
historical_high_growth = load_eurostat_data(str(historical_high_growth_raw))

# %%
modern_demography_raw = project_root / "data/raw/bd_size_total_Business_demography_by_size_class.tsv.gz"
modern_demography = load_eurostat_data(str(modern_demography_raw))
# %%
modern_survival_raw = project_root / "data/raw/bd_size_Y1_Y2_Y3.tsv.gz"
modern_survival = load_eurostat_data(str(modern_survival_raw))
# %%
modern_high_growth_raw = project_root / "data/raw/bd_hg_High_growth_enterprises_and_related_employment.tsv.gz"
modern_high_growth = load_eurostat_data(str(modern_high_growth_raw))
# %%
employment_raw = project_root / "data/raw/nama_10_a64_e_Employment_by_detailed_industry.tsv.gz"
employment = load_eurostat_data(str(employment_raw))
# %%
capital_fotmation_raw = project_root / "data/raw/nama_10_a64_p5_Capital_formation_by_industry.tsv.gz"
capital_formation = load_eurostat_data(str(capital_fotmation_raw))
# %%
