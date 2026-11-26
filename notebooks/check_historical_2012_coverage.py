# %%
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from data.load_eurostat import load_eurostat_data

main_countries = [
    "AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
    "IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK",
]

main_nace = [
    "B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N",
]

historical_demography = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"
    )
)

coverage_2012_mask = (
    historical_demography["geo"].isin(main_countries)
    & historical_demography["nace_r2"].isin(main_nace)
    & (historical_demography["sizeclas"] == "TOTAL")
    & (historical_demography["year"] == 2012)
    & historical_demography["indic_sb"].isin(["V97020", "V97030"])
)

coverage_2012 = (
    historical_demography.loc[coverage_2012_mask]
    .groupby("indic_sb")["value"]
    .count()
)

print(coverage_2012)

# %%
historical_high_growth = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_9pm_r2_High_growth_enterprises.tsv.gz"
    )
)

high_growth_2012_mask = (
    historical_high_growth["geo"].isin(main_countries)
    & historical_high_growth["nace_r2"].isin(main_nace)
    & (historical_high_growth["year"] == 2012)
    & (historical_high_growth["indic_sb"] == "V97460")
)

high_growth_2012 = historical_high_growth.loc[
    high_growth_2012_mask
].copy()

print("High-growth share, 2012:", high_growth_2012["value"].count())
# %%
missing_high_growth_2012 = high_growth_2012.loc[
    high_growth_2012["value"].isna(),
    ["geo", "nace_r2", "year", "value_raw", "flag"],
].copy()

print(missing_high_growth_2012.to_string(index=False))
print("Rows selected:", len(high_growth_2012))
# %%
historical_horizons = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_9bd_sz_cl_r2_survival_employment_growth_Y1_Y2_Y3.tsv.gz"
    )
)

survival_2012_mask = (
    historical_horizons["geo"].isin(main_countries)
    & historical_horizons["nace_r2"].isin(main_nace)
    & (historical_horizons["sizeclas"] == "TOTAL")
    & (historical_horizons["year"] == 2012)
    & historical_horizons["indic_sb"].isin(
        ["V97041", "V97042", "V97043"]
    )
)

survival_2012 = historical_horizons.loc[survival_2012_mask].copy()

survival_2012["valid_value"] = survival_2012["value"].where(
    survival_2012["value"].between(0, 100)
)

print(
    survival_2012.groupby("indic_sb").agg(
        available=("value", "count"),
        valid=("valid_value", "count"),
    )
)
# %%
