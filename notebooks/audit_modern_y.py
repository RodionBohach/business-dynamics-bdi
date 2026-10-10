# %%
from pathlib import Path

import sys
import pandas as pd

# %%
from pathlib import Path

import sys
import pandas as pd
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
# %%

from data.load_eurostat import load_eurostat_data
# %%
modern_demography_path = project_root / "data/raw/bd_size_total_Business_demography_by_size_class.tsv.gz"
modern_demography = load_eurostat_data(str(modern_demography_path))
from data.load_eurostat import load_eurostat_data
# %%
modern_demography_path = project_root / "data/raw/bd_size_total_Business_demography_by_size_class.tsv.gz"
modern_demography = load_eurostat_data(str(modern_demography_path))

modern_survival_path = project_root / "data/raw/bd_size_Y1_Y2_Y3.tsv.gz"
modern_survival = load_eurostat_data(str(modern_survival_path))

modern_high_growth_path = project_root / "data/raw/bd_hg_High_growth_enterprises_and_related_employment.tsv.gz"
modern_high_growth = load_eurostat_data(str(modern_high_growth_path))
# %%
modern_demography_mask = (modern_demography["indic_sbs"].isin(["ENT_BRTHR_PC", "ENT_DTHR_PC"])) & (modern_demography['age']=="TOTAL") & (modern_demography['sizeclas']=="TOTAL")
modern_demography_core = modern_demography[modern_demography_mask].copy()
# %%
modern_survival_mask = (modern_survival["indic_sbs"] == "ENT_SRVLR_BRTH_PC") & (modern_survival['age']=="Y3") & (modern_survival['sizeclas']=="TOTAL")
modern_survival_core = modern_survival[modern_survival_mask].copy()
# %%
modern_high_growth_mask = (modern_high_growth["indic_sbs"] == "ENT_HGRWR_PC") 
modern_high_growth_core = modern_high_growth[modern_high_growth_mask].copy()
# %%
common_columns = ['freq', 'indic_sbs', 'nace_r2', 'geo', 'year', 'value_raw', 'value', 'flag']
# %%
modern_demography_common = modern_demography_core[common_columns].copy()
modern_survival_common = modern_survival_core[common_columns].copy()
modern_high_growth_common = modern_high_growth_core[common_columns].copy()

# %%
modern_y_long = pd.concat([modern_demography_common, modern_survival_common, modern_high_growth_common], ignore_index=True)
# %%
modern_indicator_mapping = {
    'ENT_BRTHR_PC': "birth_rate",
    'ENT_DTHR_PC': "death_rate",
    'ENT_SRVLR_BRTH_PC': "survival_3y",
    'ENT_HGRWR_PC': "high_growth_share",
}
# %%
modern_y_long["component"] = modern_y_long["indic_sbs"].map(modern_indicator_mapping)
# %%
main_countries = ["AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
"IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK"]
main_nace = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N"]

# %%
country_mask = modern_y_long["geo"].isin(main_countries)
nace_mask = modern_y_long["nace_r2"].isin(main_nace)
year_mask = modern_y_long["year"].between(2021, 2024)
# %%
modern_sample_mask = country_mask & nace_mask & year_mask
# %%
modern_sample_long = modern_y_long[modern_sample_mask].copy()
assert modern_sample_long.shape == (3840, 9), "Unexpected modern sample shape"
assert modern_sample_long["component"].isna().sum() == 0, "Unmapped indicators"
assert modern_sample_long.duplicated(
    subset=["geo", "nace_r2", "year", "component"],
    keep=False,
).sum() == 0, "Duplicate modern sample keys"
# %%
coverage_counts = modern_sample_long.groupby(['year',  'component'])['value'].count()
# %%
modern_panel_audit = modern_sample_long.pivot(index=['geo', 'nace_r2', 'year'], columns='component', values='value').reset_index()
# %%
modern_panel_audit['complete_case'] = modern_panel_audit[['birth_rate', 'death_rate', 'survival_3y', 'high_growth_share']].notnull().all(axis=1)
# %%
modern_coverage_summary = modern_panel_audit.groupby('year')['complete_case'].agg(['size', 'sum']).reset_index()
# %%
modern_coverage_summary = modern_coverage_summary.rename(columns = {'size': 'expected_observations', 'sum': 'complete_observations'})
# %%
modern_coverage_summary['completeness_pct'] = (modern_coverage_summary['complete_observations'] / modern_coverage_summary['expected_observations']) * 100
# %%
coverage_dir = project_root / "outputs/coverage"
coverage_dir.mkdir(parents=True, exist_ok=True)
modern_coverage_summary.to_csv(coverage_dir / "modern_y_coverage.csv", index=False)
# %%
component_coverage_summary = coverage_counts.reset_index(name='available_observations')
# %%
component_coverage_summary["expected_observations"] = 240
component_coverage_summary["coverage_pct"] = (component_coverage_summary["available_observations"] / component_coverage_summary["expected_observations"]) * 100
# %%
component_coverage_summary.to_csv(coverage_dir / "modern_y_component_coverage.csv", index  =False)
# %%
print(modern_coverage_summary.to_string(index=False))
# %%
