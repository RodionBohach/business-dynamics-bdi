# %%
from pathlib import Path

import pandas as pd
project_root = Path(__file__).resolve().parents[1]

# %%
bdi_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

historical_horizons = pd.read_csv(
    project_root / "data/processed/historical_survival_growth_audited_long.csv"
)
# %%
historical_horizons_mask = (historical_horizons["component"] == "survival_rate") & (historical_horizons["year"].between(2013, 2020))
historical_horizons_comparison = historical_horizons[historical_horizons_mask].copy()
# %%
survival_wide = historical_horizons_comparison.pivot(
    index=["geo", "nace_r2", "year"],
    columns="horizon",
    values="value_analytical"
).reset_index()

# %%
survival_wide.rename(columns={
    1: "survival_1y",
    2: "survival_2y",
    3: "survival_3y_new"}, inplace=True)

survival_wide.columns.name = None

# %%
horizon_comparison = pd.merge(
    bdi_panel,
    survival_wide,
    on=["geo", "nace_r2", "year"],
    how="outer",
    validate="one_to_one",
    indicator=True
)
# %%
survival_3y_difference = horizon_comparison["survival_3y_new"] - horizon_comparison["survival_3y"]
# %%
common_horizon_sample = horizon_comparison.dropna(subset=["birth_rate", "death_rate", "high_growth_share", "survival_1y", "survival_2y", "survival_3y_new"]).copy()
# %%
common_horizon_sample = common_horizon_sample.drop(columns=["_merge"])
# %%
horizon_components = [
    "birth_rate",
    "death_rate",
    "high_growth_share",
    "survival_1y",
    "survival_2y",
    "survival_3y_new",
]

horizon_means = common_horizon_sample[horizon_components].mean()

horizon_stds = common_horizon_sample[horizon_components].std(ddof=0)


# %%
horizon_z_scores = (
    common_horizon_sample[horizon_components] - horizon_means
) / horizon_stds

horizon_z_scores["death_rate"] = -horizon_z_scores["death_rate"]
# %%
common_components = [
    "birth_rate",
    "death_rate",
    "high_growth_share",
]

common_horizon_sample["bdi_survival_1y"] = horizon_z_scores[
    common_components + ["survival_1y"]
].mean(axis=1, skipna=False)

common_horizon_sample["bdi_survival_2y"] = horizon_z_scores[
    common_components + ["survival_2y"]
].mean(axis=1, skipna=False)

common_horizon_sample["bdi_survival_3y"] = horizon_z_scores[
    common_components + ["survival_3y_new"]
].mean(axis=1, skipna=False)
# %%
horizon_bdi_columns = ['bdi_survival_1y', 'bdi_survival_2y', 'bdi_survival_3y']

horizon_spearman = common_horizon_sample[['bdi_survival_1y', 'bdi_survival_2y', 'bdi_survival_3y']].corr(method='spearman')
# %%
survival_only_spearman = common_horizon_sample[['survival_1y', 'survival_2y', 'survival_3y_new']].corr(method='spearman')
# %%
common_horizon_sample["rank_s1"] = common_horizon_sample[
    "bdi_survival_1y"
].rank(ascending=False, method="average")

common_horizon_sample["rank_s2"] = common_horizon_sample[
    "bdi_survival_2y"
].rank(ascending=False, method="average")

common_horizon_sample["rank_s3"] = common_horizon_sample[
    "bdi_survival_3y"
].rank(ascending=False, method="average")

common_horizon_sample["rank_shift_s1_vs_s3"] = (
    common_horizon_sample["rank_s1"]
    - common_horizon_sample["rank_s3"]
).abs()

common_horizon_sample["rank_shift_s2_vs_s3"] = (
    common_horizon_sample["rank_s2"]
    - common_horizon_sample["rank_s3"]
).abs()

# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

horizon_spearman.to_csv(
    diagnostics_dir / "bdi_survival_horizon_spearman.csv",
    index=True,
)

survival_only_spearman.to_csv(
    diagnostics_dir / "survival_rates_horizon_spearman.csv",
    index=True,
)

common_horizon_sample[
    ["rank_shift_s1_vs_s3", "rank_shift_s2_vs_s3"]
].describe(percentiles=[0.5, 0.9, 0.95]).to_csv(
    diagnostics_dir / "bdi_survival_horizon_rank_shift_summary.csv",
    index=True,
)

common_horizon_sample.to_csv(
    diagnostics_dir / "bdi_survival_horizon_comparison.csv",
    index=False,
)
# %%
historical_horizons_comparison['birth_year'] = (historical_horizons_comparison['year'] - historical_horizons_comparison['horizon'])
# %%
cohort_survival_table = historical_horizons_comparison.pivot(
    index= ['geo', 'nace_r2', 'birth_year'],
    columns= 'horizon',
    values= 'value_analytical'
).reset_index()

cohort_survival_table = cohort_survival_table.rename(columns={1: 'survival_1y', 2: 'survival_2y', 3: 'survival_3y'})
cohort_survival_table.columns.name = None

# %%
cohort_survival_comparison = cohort_survival_table.loc[
    cohort_survival_table["birth_year"].between(2012, 2017)
].copy()

# %%
cohort_increase_mask = (
    (
        cohort_survival_comparison["survival_2y"]
        > cohort_survival_comparison["survival_1y"]
    )
    | (
        cohort_survival_comparison["survival_3y"]
        > cohort_survival_comparison["survival_2y"]
    )
)

cohort_survival_increases = cohort_survival_comparison.loc[
    cohort_increase_mask
].copy()


# %%
austria_e_cohort_audit = historical_horizons.loc[
    (historical_horizons["geo"] == "AT")
    & (historical_horizons["nace_r2"] == "E")
    & (historical_horizons["component"] == "survival_rate")
    & (
        historical_horizons["year"]
        - historical_horizons["horizon"] == 2012
    ),
    ["geo", "nace_r2", "year", "horizon",
     "value_raw", "value", "flag"],
].sort_values("horizon")

# %%
cohort_survival_comparison["survival_increases_with_age"] = (
    cohort_increase_mask
)

cohort_survival_comparison.to_csv(
    diagnostics_dir / "historical_cohort_survival_comparison.csv",
    index=False,
)

cohort_survival_increases.to_csv(
    diagnostics_dir / "historical_cohort_survival_increases.csv",
    index=False,
)

austria_e_cohort_audit.to_csv(
    diagnostics_dir / "austria_e_2012_cohort_audit.csv",
    index=False,
)
# %%
