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
historical_growth_comparison = historical_horizons.loc[historical_horizons['year'].between(2013, 2020)].copy()
# %%
growth_horizon_wide = historical_growth_comparison.pivot(
    index=["geo", "nace_r2", "year"],
    columns= ["component", "horizon"],
    values= "value_analytical"
)
# %%
growth_horizon_wide.columns = [
    "survival_1y",
    "survival_2y",
    "survival_3y_new",
    "employment_growth_1y",
    "employment_growth_2y",
    "employment_growth_3y",
]

growth_horizon_wide = growth_horizon_wide.reset_index()
# %%
growth_comparison = pd.merge(bdi_panel, growth_horizon_wide, on= ['geo', 'nace_r2', 'year'], how='outer', validate='one_to_one', indicator=True)
# %%
growth_comparison_components = [
    'birth_rate', 'death_rate', 'high_growth_share',
'survival_1y', 'survival_2y', 'survival_3y_new',
'employment_growth_1y', 'employment_growth_2y', 'employment_growth_3y'
]
common_growth_sample = growth_comparison.dropna(
    subset=growth_comparison_components
).copy()

common_growth_sample = common_growth_sample.drop(columns=["_merge"])

# %%
growth_comparison_means = common_growth_sample[
    growth_comparison_components
].mean()

growth_comparison_stds = common_growth_sample[
    growth_comparison_components
].std(ddof=0)
# %%
growth_z_scores = (
    common_growth_sample[growth_comparison_components]
    - growth_comparison_means
) / growth_comparison_stds

growth_z_scores["death_rate"] = -growth_z_scores["death_rate"]
# %%
survival_columns = {
    1: "survival_1y",
    2: "survival_2y",
    3: "survival_3y_new",
}

for horizon, survival_column in survival_columns.items():
    common_growth_sample[f"bdi_s{horizon}_high_growth"] = (
        growth_z_scores[
            [
                "birth_rate",
                "death_rate",
                survival_column,
                "high_growth_share",
            ]
        ].mean(axis=1, skipna=False)
    )

    common_growth_sample[f"bdi_s{horizon}_survivor_growth"] = (
        growth_z_scores[
            [
                "birth_rate",
                "death_rate",
                survival_column,
                f"employment_growth_{horizon}y",
            ]
        ].mean(axis=1, skipna=False)
    )
# %%
spearmen_s1 = common_growth_sample[['bdi_s1_high_growth', 'bdi_s1_survivor_growth']].corr(method="spearman")
spearmen_s2 = common_growth_sample[['bdi_s2_high_growth', 'bdi_s2_survivor_growth']].corr(method="spearman")
spearmen_s3 = common_growth_sample[['bdi_s3_high_growth', 'bdi_s3_survivor_growth']].corr(method="spearman")
growth_component_comparison = pd.DataFrame({
    "horizon": [1, 2, 3],
    "spearman_rho": [
        spearmen_s1.iloc[0, 1],
        spearmen_s2.iloc[0, 1],
        spearmen_s3.iloc[0, 1],
    ],
    "n_observations": len(common_growth_sample),
})

# %%
spearmen_g1 = common_growth_sample[['high_growth_share', 'employment_growth_1y']].corr(method='spearman')
spearmen_g2 = common_growth_sample[['high_growth_share', 'employment_growth_2y']].corr(method='spearman')
spearmen_g3 = common_growth_sample[['high_growth_share', 'employment_growth_3y']].corr(method='spearman')

growth_indicator_comparison = pd.DataFrame({
    "horizon": [1, 2, 3],
    "spearman_rho": [
        spearmen_g1.iloc[0, 1],
        spearmen_g2.iloc[0, 1],
        spearmen_g3.iloc[0, 1],
    ],
    "n_observations": len(common_growth_sample),
})


# %%
rank_shift_summaries = []

for horizon in [1, 2, 3]:
    rank_high_growth = common_growth_sample[
        f"bdi_s{horizon}_high_growth"
    ].rank(ascending=False, method="average")

    rank_survivor_growth = common_growth_sample[
        f"bdi_s{horizon}_survivor_growth"
    ].rank(ascending=False, method="average")

    shift_column = f"rank_shift_growth_s{horizon}"

    common_growth_sample[shift_column] = (
        rank_high_growth - rank_survivor_growth
    ).abs()

    summary = common_growth_sample[shift_column].describe(
        percentiles=[0.5, 0.9, 0.95]
    )
    summary["horizon"] = horizon
    rank_shift_summaries.append(summary)

growth_rank_shift_summary = pd.DataFrame(
    rank_shift_summaries
).set_index("horizon")

growth_rank_shift_summary.index = (
    growth_rank_shift_summary.index.astype(int)
)
# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

growth_component_comparison.to_csv(
    diagnostics_dir / "bdi_growth_component_spearman.csv",
    index=False,
)

growth_indicator_comparison.to_csv(
    diagnostics_dir / "growth_indicators_spearman.csv",
    index=False,
)

growth_rank_shift_summary.to_csv(
    diagnostics_dir / "bdi_growth_component_rank_shifts.csv",
    index=True,
)

common_growth_sample.to_csv(
    diagnostics_dir / "bdi_growth_component_comparison.csv",
    index=False,
)
# %%
growth_normalization_parameters = pd.DataFrame({
    "mean": growth_comparison_means,
    "std": growth_comparison_stds,
})

growth_normalization_parameters["direction"] = 1
growth_normalization_parameters.loc["death_rate", "direction"] = -1
growth_normalization_parameters["reference_n"] = len(common_growth_sample)

growth_normalization_parameters.rename_axis("component").to_csv(
    diagnostics_dir / "growth_comparison_normalization_parameters.csv",
    index=True,
)
# %%
