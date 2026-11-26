
# %%
from pathlib import Path

import sys
import pandas as pd
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

# %%
from data.load_eurostat import load_eurostat_data
modern_survival = load_eurostat_data(str(project_root / "data/raw/bd_size_Y1_Y2_Y3.tsv.gz"))
historical_demography = load_eurostat_data(str(project_root / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"))

# %%
survival_mask = (modern_survival["indic_sbs"] == "ENT_SRVLR_BRTH_PC") & (modern_survival["sizeclas"] == "TOTAL")
survival_rates = modern_survival[survival_mask].copy()
survival_coverage = survival_rates.groupby(['age', 'year'])['value'].count()
# %%
main_countries = ["AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
"IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK"]
main_nace = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N"]

survival_rates_mask = (survival_rates['geo'].isin(main_countries)) & (survival_rates['nace_r2'].isin(main_nace))
survival_rates_core = survival_rates[survival_rates_mask].copy()
survival_main_coverage = survival_rates_core.groupby(['age', 'year'])['value'].count()
# %%
survival_horizon_coverage = survival_main_coverage.reset_index(
    name="available_observations"
)

survival_horizon_coverage["expected_observations"] = 240
survival_horizon_coverage["coverage_pct"] = (
    survival_horizon_coverage["available_observations"]
    / survival_horizon_coverage["expected_observations"]
    * 100
)

coverage_dir = project_root / "outputs/coverage"
coverage_dir.mkdir(parents=True, exist_ok=True)

survival_horizon_coverage.to_csv(
    coverage_dir / "survival_horizon_coverage.csv",
    index=False,
)
# %%
historical_horizons = load_eurostat_data(str(project_root / "data/raw/bd_9bd_sz_cl_r2_survival_employment_growth_Y1_Y2_Y3.tsv.gz"))
modern_horizons = load_eurostat_data(str(project_root / "data/raw/bd_size_survival_employment_growth_Y1_Y2_Y3.tsv.gz"))
# %%
historical_horizons_mask = (historical_horizons["geo"].isin(main_countries)) & (historical_horizons["sizeclas"] == "TOTAL") & (historical_horizons['nace_r2'].isin(main_nace))
historical_horizons_core = historical_horizons[historical_horizons_mask].copy()

modern_horizons_mask = (modern_horizons["geo"].isin(main_countries)) & (modern_horizons["sizeclas"] == "TOTAL") & (modern_horizons['nace_r2'].isin(main_nace))
modern_horizons_core = modern_horizons[modern_horizons_mask].copy()
# %%
historical_coverage = (
    historical_horizons_core
    .groupby(["indic_sb", "year"])["value"]
    .count()
)

modern_coverage = (
    modern_horizons_core
    .groupby(["indic_sbs", "age", "year"])["value"]
    .count()
)
# %%
historical_coverage_table = historical_coverage.reset_index(
    name="available_observations"
)
modern_coverage_table = modern_coverage.reset_index(
    name="available_observations"
)

for coverage_table in [historical_coverage_table, modern_coverage_table]:
    coverage_table["expected_observations"] = 240
    coverage_table["coverage_pct"] = (
        coverage_table["available_observations"]
        / coverage_table["expected_observations"]
        * 100
    )

coverage_dir = project_root / "outputs/coverage"
coverage_dir.mkdir(parents=True, exist_ok=True)

historical_coverage_table.to_csv(
    coverage_dir / "historical_survival_growth_coverage.csv",
    index=False,
)
modern_coverage_table.to_csv(
    coverage_dir / "modern_survival_growth_coverage.csv",
    index=False,
)
# %%
historical_survival_rates = historical_horizons_core[historical_horizons_core['indic_sb'].isin(["V97041", "V97042", "V97043"])].copy()
outside_range_mask = (
    (historical_survival_rates["value"] < 0)
    | (historical_survival_rates["value"] > 100)
)

historical_survival_anomalies = historical_survival_rates.loc[
    outside_range_mask,
    ["geo", "nace_r2", "year", "indic_sb", "value_raw", "value", "flag"],
].copy()

print(historical_survival_anomalies.to_string(index=False))
print(historical_survival_anomalies.shape)

diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

historical_survival_anomalies.to_csv(
    diagnostics_dir / "historical_survival_out_of_range.csv",
    index=False,
)
# %%
anomaly_summary = (
    historical_survival_anomalies
    .groupby(["geo", "year", "indic_sb"])
    .size()
    .reset_index(name="anomaly_count")
)

print(anomaly_summary.to_string(index=False))

anomaly_summary.to_csv(
    diagnostics_dir / "historical_survival_anomaly_summary.csv",
    index=False,
)
# %%
modern_survival_rates = modern_horizons_core[modern_horizons_core['indic_sbs'].isin(["ENT_SRVLR_BRTH_PC"])].copy()
modern_survival_anomalies_mask = ((modern_survival_rates["value"] < 0) | (modern_survival_rates["value"] > 100))
modern_survival_anomalies = modern_survival_rates.loc[modern_survival_anomalies_mask, ["geo", "nace_r2", "age", "year", "value_raw", "value", "flag"]].copy()
# %%
modern_survival_anomalies.to_csv(
    diagnostics_dir / "modern_survival_out_of_range.csv",
    index=False,
)
# %%
norway_d_mask = (
    (modern_survival_rates["geo"] == "NO")
    & (modern_survival_rates["nace_r2"] == "D")
)

norway_d_survival_audit = modern_survival_rates.loc[
    norway_d_mask,
    ["geo", "nace_r2", "age", "year", "value_raw", "value", "flag"],
].sort_values(["year", "age"]).copy()

print(norway_d_survival_audit.to_string(index=False))

norway_d_survival_audit.to_csv(
    diagnostics_dir / "norway_d_modern_survival_audit.csv",
    index=False,
)
# %%
historical_growth_rates = historical_horizons_core[historical_horizons_core['indic_sb'].isin(["V97141", "V97142", "V97143"])].copy()
modern_growth_rates = modern_horizons_core[modern_horizons_core['indic_sbs'].isin(["GRW_EMP_SRVL_PC"])].copy()
# %%
historical_growth_top = (
    historical_growth_rates
    .sort_values("value", ascending=False)
    .groupby("indic_sb", sort=False)
    .head(5)
    .loc[:, ["geo", "nace_r2", "year", "indic_sb",
             "value_raw", "value", "flag"]]
    .copy()
)

# %%
modern_growth_top = (
    modern_growth_rates
    .sort_values("value", ascending=False)
    .groupby("age", sort=False)
    .head(5)
    .loc[:, ["geo", "nace_r2", "age", "year",
             "value_raw", "value", "flag"]]
    .copy()
)
# %%
historical_growth_top.to_csv(
    diagnostics_dir / "historical_survivor_growth_top.csv",
    index=False,
)

modern_growth_top.to_csv(
    diagnostics_dir / "modern_survivor_growth_top.csv",
    index=False,
)
# %%
historical_growth_below_minus100 = historical_growth_rates.loc[
    historical_growth_rates["value"] < -100
].copy()

modern_growth_below_minus100 = modern_growth_rates.loc[
    modern_growth_rates["value"] < -100
].copy()
# %%
historical_growth_rates["below_minus_100"] = (
    historical_growth_rates["value"] < -100
)
historical_growth_rates["equal_minus_100"] = (
    historical_growth_rates["value"] == -100
)

historical_growth_rates_extreme = (
    historical_growth_rates.groupby("indic_sb")
    .agg(
        available_observations=("value", "count"),
        min_value=("value", "min"),
        max_value=("value", "max"),
        below_minus_100_count=("below_minus_100", "sum"),
        equal_minus_100_count=("equal_minus_100", "sum"),
    )
    .reset_index()
)
# %%
modern_growth_rates["below_minus_100"] = (
    modern_growth_rates["value"] < -100
)
modern_growth_rates["equal_minus_100"] = (
    modern_growth_rates["value"] == -100
)
modern_growth_rates_extreme = (
    modern_growth_rates.groupby("age")
    .agg(
        available_observations=("value", "count"),
        min_value=("value", "min"),
        max_value=("value", "max"),
        below_minus_100_count=("below_minus_100", "sum"),
        equal_minus_100_count=("equal_minus_100", "sum"),
    )
    .reset_index()
)
# %%
historical_growth_rates_extreme.to_csv(
    diagnostics_dir / "historical_survivor_growth_extreme.csv",
    index=False,
)

modern_growth_rates_extreme.to_csv(
    diagnostics_dir / "modern_survivor_growth_extreme.csv",
    index=False,
)
# %%
historical_component_mapping = {
    "V97041": "survival_rate",
    "V97042": "survival_rate",
    "V97043": "survival_rate",
    "V97141": "survivor_employment_growth",
    "V97142": "survivor_employment_growth",
    "V97143": "survivor_employment_growth",
}

historical_horizon_mapping = {
    "V97041": 1,
    "V97042": 2,
    "V97043": 3,
    "V97141": 1,
    "V97142": 2,
    "V97143": 3,
}
# %%
historical_horizons_core["component"] = historical_horizons_core["indic_sb"].map(historical_component_mapping)
historical_horizons_core["horizon"] = historical_horizons_core["indic_sb"].map(historical_horizon_mapping)
# %%
modern_component_mapping = {
    "ENT_SRVLR_BRTH_PC": "survival_rate",
    "GRW_EMP_SRVL_PC": "survivor_employment_growth",
    }
modern_horizon_mapping = {
    "Y1": 1,
    "Y2": 2,
    "Y3": 3,
}
# %%
modern_horizons_core["component"] = modern_horizons_core["indic_sbs"].map(modern_component_mapping)
modern_horizons_core["horizon"] = modern_horizons_core["age"].map(modern_horizon_mapping)
# %%
historical_horizons_core["value_analytical"] = (
    historical_horizons_core["value"]
)

historical_horizons_core["survival_out_of_range"] = (
    (historical_horizons_core["component"] == "survival_rate")
    & (
        (historical_horizons_core["value"] < 0)
        | (historical_horizons_core["value"] > 100)
    )
)

historical_horizons_core.loc[
    historical_horizons_core["survival_out_of_range"],
    "value_analytical",
] = pd.NA
# %%
modern_horizons_core ["value_analytical"] = (modern_horizons_core["value"])

modern_horizons_core["survival_out_of_range"] = (
    (modern_horizons_core["component"] == "survival_rate")
    & (
        (modern_horizons_core["value"] < 0)
        | (modern_horizons_core["value"] > 100)
    )
)

modern_horizons_core.loc[
    modern_horizons_core["survival_out_of_range"],
    "value_analytical",
] = pd.NA
# %%
historical_analytical_coverage = (
    historical_horizons_core.groupby(["component", "horizon", "year"])["value_analytical"]
    .count()
)

modern_analytical_coverage = (
    modern_horizons_core.groupby(["component", "horizon", "year"])["value_analytical"]
    .count()
)
# %%
historical_analytical_coverage_table = (
    historical_analytical_coverage.reset_index(
        name="available_observations"
    )
)

modern_analytical_coverage_table = (
    modern_analytical_coverage.reset_index(
        name="available_observations"
    )
)

for coverage_table in [
    historical_analytical_coverage_table,
    modern_analytical_coverage_table,
]:
    coverage_table["expected_observations"] = 240
    coverage_table["coverage_pct"] = (
        coverage_table["available_observations"]
        / coverage_table["expected_observations"]
        * 100
    )

coverage_dir = project_root / "outputs/coverage"
coverage_dir.mkdir(parents=True, exist_ok=True)

historical_analytical_coverage_table.to_csv(
    coverage_dir / "historical_analytical_horizon_coverage.csv",
    index=False,
)

modern_analytical_coverage_table.to_csv(
    coverage_dir / "modern_analytical_horizon_coverage.csv",
    index=False,
)
# %%
processed_dir = project_root / "data/processed"
processed_dir.mkdir(parents=True, exist_ok=True)

historical_horizons_core.to_csv(
    processed_dir / "historical_survival_growth_audited_long.csv",
    index=False,
)

modern_horizons_core.to_csv(
    processed_dir / "modern_survival_growth_audited_long.csv",
    index=False,
)


# %%
