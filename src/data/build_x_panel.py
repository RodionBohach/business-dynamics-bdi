# %%
from load_eurostat import load_eurostat_data
import pandas as pd
# %%
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
# %%
economic_accounts_path = project_root / "data/raw/nama_10_a64_Gross_value_added_and_income.tsv.gz"
economic_accounts = load_eurostat_data(economic_accounts_path)
employment_path = project_root / "data/raw/nama_10_a64_e_Employment_by_detailed_industry.tsv.gz"
employment = load_eurostat_data(employment_path)
capital_formation_path = project_root / "data/raw/nama_10_a64_p5_Capital_formation_by_industry.tsv.gz"
capital_formation = load_eurostat_data(capital_formation_path)
# %%
main_countries = ["AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
"IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK"]
main_nace = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N"]
# %%
economic_accounts_mask = economic_accounts["geo"].isin(main_countries) & economic_accounts["nace_r2"].isin(main_nace) & economic_accounts["year"].between(2012, 2020)
economic_accounts_sample = economic_accounts[economic_accounts_mask].copy()
employment_mask = employment["geo"].isin(main_countries) & employment["nace_r2"].isin(main_nace) & employment["year"].between(2012, 2020)
employment_sample = employment[employment_mask].copy()
capital_formation_mask = capital_formation["geo"].isin(main_countries) & capital_formation["nace_r2"].isin(main_nace) & capital_formation["year"].between(2012, 2020)
capital_formation_sample = capital_formation[capital_formation_mask].copy()
# %%
x_indicator_mapping = {
    'B1G': "gross_value_added",
    'P1': "output",
    'D1': "compensation",
    'B2A3N': "net_operating_surplus_mixed_income",
    'EMP_DC': "employment",
    'SAL_DC': "employees",
    'P51G': "gfcf"
}
# %%
economic_accounts_sample['variable'] = economic_accounts_sample['na_item'].map(x_indicator_mapping)
employment_sample['variable'] = employment_sample['na_item'].map(x_indicator_mapping)
capital_formation_sample['variable'] = capital_formation_sample['na_item'].map(x_indicator_mapping)
# %%
x_common_columns = ['freq', 'unit', 'nace_r2', 'na_item', 'geo', 'year', 'value_raw', 'value', 'flag', 'variable']
# %%
economic_accounts_common = economic_accounts_sample[x_common_columns].copy()
employment_common = employment_sample[x_common_columns].copy()
capital_formation_common = capital_formation_sample[x_common_columns].copy()
# %%
x_long = pd.concat([economic_accounts_common, employment_common, capital_formation_common], ignore_index=True)
# %%
x_base_panel = x_long.pivot(index=['geo', 'nace_r2', 'year'], columns='variable', values='value').reset_index()
# %%
x_base_panel.columns.name = None

# %%
x_derived_panel = x_base_panel.copy()
x_derived_panel['investment_intensity'] = (x_derived_panel['gfcf'] / x_derived_panel['gross_value_added']) * 100
# %%
x_derived_panel["negative_gfcf"] = x_derived_panel["gfcf"] < 0
# %%
x_derived_panel['labour_share'] = (x_derived_panel['compensation'] / x_derived_panel['gross_value_added'])* 100
# %%
x_derived_panel['average_compensation'] = (x_derived_panel['compensation'] / x_derived_panel['employees']) * 1000
# %%
x_derived_panel['value_added_ratio'] = (x_derived_panel['gross_value_added'] / x_derived_panel['output']) * 100
# %%
x_derived_panel['gfcf_per_employed'] = (x_derived_panel['gfcf'] / x_derived_panel['employment']) * 1000
# %%
x_derived_panel['labour_productivity'] = (x_derived_panel['gross_value_added'] / x_derived_panel['employment']) * 1000
# %%
x_derived_panel = x_derived_panel.sort_values(['geo', 'nace_r2', 'year'])
# %%
x_derived_panel['employment_lag1'] = x_derived_panel.groupby(["geo", "nace_r2"])['employment'].shift(1)
# %%
x_derived_panel['employment_growth'] = (x_derived_panel['employment'] / x_derived_panel['employment_lag1'] -1   )* 100
# %%
x_derived_panel['net_operating_surplus_mixed_income_margin'] = (x_derived_panel['net_operating_surplus_mixed_income'] / x_derived_panel['output']) * 100
# %%
x_derived_panel_mask = x_derived_panel['year'].between(2013, 2020)
x_panel = x_derived_panel[x_derived_panel_mask].copy()
# %%
assert x_panel.shape == (1920, 20), "Unexpected X-panel shape"
assert x_panel.duplicated(subset=['geo', 'nace_r2', 'year'], keep=False).sum() == 0, "Duplicate rows in X-panel"
assert x_panel.isna().sum().sum() == 0, "Unexpected missing values in X-panel"
processed_dir = project_root / "data/processed"
processed_dir.mkdir(parents=True, exist_ok=True)
final_dir = project_root / "data/final"
final_dir.mkdir(parents=True, exist_ok=True)
x_long.to_csv(processed_dir / "X_main_long.csv", index=False)
x_base_panel.to_csv(processed_dir / 'X_base_panel.csv', index=False)
x_panel.to_csv(final_dir / 'X_panel.csv', index=False)
print("X-panel saved:", x_panel.shape)
