# %%
from load_eurostat import load_eurostat_data
import pandas as pd
# %%
from pathlib import Path
Path.cwd()
# %%
project_root = Path(__file__).resolve().parents[2]
# %%
raw_path = project_root / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"
# %%
historical_demography = load_eurostat_data(raw_path)

# %%
historical_high_growth_raw = project_root / "data/raw/bd_9pm_r2_High_growth_enterprises.tsv.gz"
# %%
historical_high_growth = load_eurostat_data(historical_high_growth_raw)
# %%
demography_mask = historical_demography["indic_sb"].isin(['V97020', 'V97030', 'V97043'])
# %%
demography_core = historical_demography[demography_mask].copy()
# %%
high_growth_mask = historical_high_growth["indic_sb"].isin(['V97460'])
high_growth_core = historical_high_growth[high_growth_mask].copy()
# %%
demography_core = demography_core.drop(columns=["sizeclas"])
# %%
historical_y_long = pd.concat([demography_core, high_growth_core],ignore_index=True )
# %%
indicator_mapping = {
    'V97020': "birth_rate",
    'V97030': "death_rate",
    'V97043': "survival_3y",
    'V97460': "high_growth_share",
}
# %%
historical_y_long["component"] = historical_y_long["indic_sb"].map(indicator_mapping)
# %%
main_countries = ["AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
"IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK"]
# %%
main_nace = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N"]
# %%
country_mask = historical_y_long["geo"].isin(main_countries)
nace_mask = historical_y_long["nace_r2"].isin(main_nace)
year_mask = historical_y_long["year"].between(2013, 2020)
# %%
main_sample_mask = country_mask & nace_mask & year_mask
# %%
y_main_long = historical_y_long[main_sample_mask].copy()
# %%
quarantine_mask = (y_main_long['geo'] == "RO") & (y_main_long['nace_r2'].isin(["J", "N"])) & (y_main_long['year'] == 2013) & (y_main_long['component'] == "survival_3y")
# %%
y_main_long['value_analytical'] = y_main_long['value']
y_main_long['quarantined'] = quarantine_mask
y_main_long.loc[quarantine_mask, "value_analytical"] = pd.NA
# %%
y_panel = y_main_long.pivot(index=['geo', 'nace_r2', 'year'], columns='component', values='value_analytical').reset_index()
# %%
y_panel.columns.name = None
# %%
processed_dir = project_root / "data/processed"
processed_dir.mkdir(parents=True, exist_ok=True)
final_dir = project_root / "data/final"
final_dir.mkdir(parents=True, exist_ok=True)
# %%
assert y_panel.shape == (1920, 7), "Unexpected Y-panel shape"
assert y_panel.duplicated(subset=['geo', 'nace_r2', 'year'], keep=False).sum() == 0, "Duplicate rows in Y-panel"
assert y_panel["survival_3y"].isna().sum() == 2, "Unexpected survival missing count"
assert y_panel.isna().sum().sum() == 2, "Unexpected total missing count"
y_main_long.to_csv(processed_dir / "Y_main_long.csv", index=False)
y_panel.to_csv(final_dir / "Y_panel.csv", index=False)
print("Y-panel saved:", y_panel.shape)
# %%
y_panel_check = pd.read_csv(final_dir / "Y_panel.csv")
# %%
