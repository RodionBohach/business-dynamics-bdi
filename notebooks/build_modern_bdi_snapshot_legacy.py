# %%
from pathlib import Path
import sys

import pandas as pd

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from data.load_eurostat import load_eurostat_data

# %%
modern_horizons = pd.read_csv(
    project_root
    / "data/processed/modern_survival_growth_audited_long.csv"
)

modern_demography = load_eurostat_data(
    project_root
    / "data/raw/bd_size_total_Business_demography_by_size_class.tsv.gz"
)

modern_high_growth = load_eurostat_data(
    project_root
    / "data/raw/bd_hg_High_growth_enterprises_and_related_employment.tsv.gz"
)
# %%
main_countries = [
    "AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
    "IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK",
]

main_nace = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N"]

demography_mask = (
    modern_demography["geo"].isin(main_countries)
    & modern_demography["nace_r2"].isin(main_nace)
    & modern_demography["year"].between(2021, 2024)
    & (modern_demography["age"] == "TOTAL")
    & (modern_demography["sizeclas"] == "TOTAL")
    & modern_demography["indic_sbs"].isin(
        ["ENT_BRTHR_PC", "ENT_DTHR_PC"]
    )
)

modern_demography_core = modern_demography.loc[
    demography_mask
].copy()

modern_demography_core["component"] = (
    modern_demography_core["indic_sbs"].map({
        "ENT_BRTHR_PC": "birth_rate",
        "ENT_DTHR_PC": "death_rate",
    })
)

# %%
high_growth_mask = (
    modern_high_growth["geo"].isin(main_countries)
    & modern_high_growth["nace_r2"].isin(main_nace)
    & modern_high_growth["year"].between(2021, 2024)
    & (modern_high_growth["indic_sbs"] == "ENT_HGRWR_PC")
)

modern_high_growth_core = modern_high_growth.loc[
    high_growth_mask
].copy()

modern_high_growth_core["component"] = "high_growth_share"
# %%
common_columns = ["geo", "nace_r2", "year", "component", "value"]

modern_common_long = pd.concat(
    [
        modern_demography_core[common_columns],
        modern_high_growth_core[common_columns],
    ],
    ignore_index=True,
)

modern_common_wide = modern_common_long.pivot(
    index=["geo", "nace_r2", "year"],
    columns="component",
    values="value",
).reset_index()

modern_common_wide.columns.name = None
# %%
modern_survival_long = modern_horizons.loc[
    modern_horizons["component"] == "survival_rate"
].copy()

modern_survival_wide = modern_survival_long.pivot(
    index=["geo", "nace_r2", "year"],
    columns="horizon",
    values="value_analytical",
).reset_index()

modern_survival_wide = modern_survival_wide.rename(
    columns={
        1: "survival_1y",
        2: "survival_2y",
        3: "survival_3y",
    }
)
modern_survival_wide.columns.name = None
# %%
modern_snapshot = modern_common_wide.merge(
    modern_survival_wide,
    on=["geo", "nace_r2", "year"],
    how="outer",
    validate="one_to_one",
    indicator=True,
)

# %%
modern_snapshot = modern_snapshot.drop(columns="_merge")

common_components = [
    "birth_rate",
    "death_rate",
    "high_growth_share",
]

for horizon in [1, 2, 3]:
    required_components = common_components + [f"survival_{horizon}y"]

    modern_snapshot[f"complete_s{horizon}"] = (
        modern_snapshot[required_components].notna().all(axis=1)
    )

modern_complete_coverage = (
    modern_snapshot.groupby("year")[
        ["complete_s1", "complete_s2", "complete_s3"]
    ].sum()
)
# %%
modern_2024_common = modern_snapshot.loc[
    (modern_snapshot["year"] == 2024)
    & modern_snapshot[
        ["complete_s1", "complete_s2", "complete_s3"]
    ].all(axis=1)
].copy()
# %%
modern_components = [
    "birth_rate",
    "death_rate",
    "high_growth_share",
    "survival_1y",
    "survival_2y",
    "survival_3y",
]

modern_means = modern_2024_common[modern_components].mean()
modern_stds = modern_2024_common[modern_components].std(ddof=0)
# %%
modern_z_scores = (
    modern_2024_common[modern_components] - modern_means
) / modern_stds

modern_z_scores["death_rate"] *= -1

for horizon in [1, 2, 3]:
    selected_components = common_components + [f"survival_{horizon}y"]

    modern_2024_common[f"bdi_s{horizon}"] = (
        modern_z_scores[selected_components].mean(
            axis=1,
            skipna=False,
        )
    )
# %%
modern_bdi_columns = ["bdi_s1", "bdi_s2", "bdi_s3"]

modern_horizon_spearman = (
    modern_2024_common[modern_bdi_columns].corr(method="spearman")
)
# %%
print(modern_horizon_spearman)
# %%
for horizon in [1, 2, 3]:
    modern_2024_common[f"rank_s{horizon}"] = (
        modern_2024_common[f"bdi_s{horizon}"]
        .rank(ascending=False, method="average")
    )

for horizon in [1, 2]:
    modern_2024_common[f"rank_shift_s{horizon}_vs_s3"] = (
        modern_2024_common[f"rank_s{horizon}"]
        - modern_2024_common["rank_s3"]
    ).abs()

modern_rank_shift_summary = modern_2024_common[
    ["rank_shift_s1_vs_s3", "rank_shift_s2_vs_s3"]
].describe(percentiles=[0.5, 0.9, 0.95])
# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

modern_2024_common.to_csv(
    diagnostics_dir / "modern_bdi_2024_horizon_comparison.csv",
    index=False,
)

modern_horizon_spearman.to_csv(
    diagnostics_dir / "modern_bdi_2024_horizon_spearman.csv",
    index=True,
)

modern_rank_shift_summary.to_csv(
    diagnostics_dir / "modern_bdi_2024_rank_shift_summary.csv",
    index=True,
)

modern_normalization_parameters = pd.DataFrame({
    "mean": modern_means,
    "std": modern_stds,
    "direction": [
        -1 if component == "death_rate" else 1
        for component in modern_components
    ],
    "reference_n": len(modern_2024_common),
})
modern_normalization_parameters.index.name = "component"

modern_normalization_parameters.to_csv(
    diagnostics_dir / "modern_bdi_2024_normalization_parameters.csv",
    index=True,
)
# %%
modern_country_summary = (
    modern_2024_common.groupby("geo")
    .agg(
        n_industries=("nace_r2", "nunique"),
        birth_rate=("birth_rate", "mean"),
        death_rate=("death_rate", "mean"),
        high_growth_share=("high_growth_share", "mean"),
        survival_1y=("survival_1y", "mean"),
        survival_2y=("survival_2y", "mean"),
        survival_3y=("survival_3y", "mean"),
        bdi_s1=("bdi_s1", "mean"),
        bdi_s2=("bdi_s2", "mean"),
        bdi_s3=("bdi_s3", "mean"),
    )
    .sort_values("bdi_s3", ascending=False)
)

descriptive_dir = project_root / "outputs/descriptive"
descriptive_dir.mkdir(parents=True, exist_ok=True)

modern_country_summary.to_csv(
    descriptive_dir / "modern_bdi_2024_country_summary.csv",
    index=True,
)
# %%
excluded_2024 = modern_snapshot.loc[
    (modern_snapshot["year"] == 2024)
    & ~modern_snapshot[
        ["complete_s1", "complete_s2", "complete_s3"]
    ].all(axis=1),
    [
        "geo",
        "nace_r2",
        "birth_rate",
        "death_rate",
        "high_growth_share",
        "survival_1y",
        "survival_2y",
        "survival_3y",
    ],
].copy()

print(excluded_2024.to_string(index=False))

excluded_2024.to_csv(
    diagnostics_dir / "modern_bdi_2024_excluded_observations.csv",
    index=False,
)
# %%
coverage_dir = project_root / "outputs/coverage"
coverage_dir.mkdir(parents=True, exist_ok=True)

modern_complete_coverage.to_csv(
    coverage_dir / "modern_bdi_complete_coverage.csv",
    index=True,
)
# %%
modern_dynamics = modern_snapshot.copy()

modern_dynamics_z_scores = (
    modern_dynamics[modern_components] - modern_means
) / modern_stds

modern_dynamics_z_scores["death_rate"] *= -1

available_years = {
    1: [2022, 2023, 2024],
    2: [2023, 2024],
    3: [2024],
}

for horizon, years in available_years.items():
    selected_components = common_components + [
        f"survival_{horizon}y"
    ]

    modern_dynamics[f"bdi_s{horizon}"] = (
        modern_dynamics_z_scores[selected_components]
        .mean(axis=1, skipna=False)
        .where(modern_dynamics["year"].isin(years))
    )
# %%
balanced_keys_by_horizon = {}

for horizon, years in available_years.items():
    index_column = f"bdi_s{horizon}"

    available_counts = (
        modern_dynamics.loc[
            modern_dynamics["year"].isin(years)
        ]
        .groupby(["geo", "nace_r2"])[index_column]
        .count()
    )

    balanced_keys = available_counts.loc[
        available_counts == len(years)
    ].index

    balanced_keys_by_horizon[horizon] = balanced_keys

    print(
        f"S{horizon}: {len(balanced_keys)} pairs, "
        f"years {years}"
    )
# %%
modern_balanced_parts = []

pair_keys = pd.MultiIndex.from_frame(
    modern_dynamics[["geo", "nace_r2"]]
)

for horizon, years in available_years.items():
    balanced_mask = (
        pair_keys.isin(balanced_keys_by_horizon[horizon])
        & modern_dynamics["year"].isin(years)
    )

    selected = modern_dynamics.loc[
        balanced_mask,
        ["geo", "nace_r2", "year", f"bdi_s{horizon}"],
    ].copy()

    selected = selected.rename(
        columns={f"bdi_s{horizon}": "bdi"}
    )
    selected["survival_horizon"] = horizon

    modern_balanced_parts.append(selected)

modern_dynamics_balanced = pd.concat(
    modern_balanced_parts,
    ignore_index=True,
)

modern_dynamics_summary = (
    modern_dynamics_balanced
    .groupby(["survival_horizon", "year"])
    .agg(
        n_observations=("bdi", "count"),
        mean_bdi=("bdi", "mean"),
        median_bdi=("bdi", "median"),
        std_bdi=("bdi", "std"),
    )
    .reset_index()
)
# %%
modern_dynamics.to_csv(
    diagnostics_dir / "modern_bdi_dynamics_available.csv",
    index=False,
)

modern_dynamics_balanced.to_csv(
    diagnostics_dir / "modern_bdi_dynamics_balanced.csv",
    index=False,
)

modern_dynamics_summary.to_csv(
    descriptive_dir / "modern_bdi_dynamics_summary.csv",
    index=False,
)
# %%
scenario_comparison = modern_2024_common.loc[
    modern_2024_common["nace_r2"].isin(["C", "J"]),
    [
        "geo",
        "nace_r2",
        "survival_3y",
        "high_growth_share",
        "birth_rate",
        "death_rate",
    ],
].copy()

for industry in ["C", "J"]:
    industry_comparison = (
        scenario_comparison.loc[
            scenario_comparison["nace_r2"] == industry
        ]
        .sort_values("survival_3y", ascending=False)
    )

    print(f"\nIndustry: {industry}")
    print(industry_comparison.round(2).to_string(index=False))
# %%
scenario_comparison.to_csv(
    diagnostics_dir / "modern_2024_c_j_scenario_comparison.csv",
    index=False,
)

print(
    scenario_comparison.loc[
        scenario_comparison["nace_r2"] == "J"
    ]
    .sort_values("survival_3y", ascending=False)
    .round(2)
    .to_string(index=False)
)
# %%
minimum_survival = 60

eligible_options = scenario_comparison.loc[
    scenario_comparison["survival_3y"] >= minimum_survival
].copy()

for industry in ["C", "J"]:
    print(f"\nIndustry: {industry}")

    print(
        eligible_options.loc[
            eligible_options["nace_r2"] == industry
        ]
        .sort_values("survival_3y", ascending=False)
        .round(2)
        .to_string(index=False)
    )
# %%
eligible_options["pareto_optimal"] = False

for industry in ["C", "J"]:
    industry_options = eligible_options.loc[
        eligible_options["nace_r2"] == industry
    ]

    for row_index, row in industry_options.iterrows():
        dominated_by_another = (
            (
                industry_options["survival_3y"]
                >= row["survival_3y"]
            )
            & (
                industry_options["high_growth_share"]
                >= row["high_growth_share"]
            )
            & (
                (
                    industry_options["survival_3y"]
                    > row["survival_3y"]
                )
                | (
                    industry_options["high_growth_share"]
                    > row["high_growth_share"]
                )
            )
        ).any()

        eligible_options.loc[row_index, "pareto_optimal"] = (
            not dominated_by_another
        )

print(
    eligible_options.loc[
        eligible_options["pareto_optimal"],
        ["geo", "nace_r2", "survival_3y", "high_growth_share"],
    ].to_string(index=False)
)
# %%
preference_comparison = eligible_options.loc[
    eligible_options["pareto_optimal"]
].copy()

survival_z = (
    preference_comparison["survival_3y"]
    - modern_means["survival_3y"]
) / modern_stds["survival_3y"]

growth_z = (
    preference_comparison["high_growth_share"]
    - modern_means["high_growth_share"]
) / modern_stds["high_growth_share"]

scenarios = {
    "survival_priority": 0.75,
    "equal_priority": 0.50,
    "growth_priority": 0.25,
}

for scenario, survival_weight in scenarios.items():
    preference_comparison[scenario] = (
        survival_weight * survival_z
        + (1 - survival_weight) * growth_z
    )

print(
    preference_comparison[
        [
            "geo",
            "nace_r2",
            "survival_priority",
            "equal_priority",
            "growth_priority",
        ]
    ].round(3).to_string(index=False)
)
# %%
eligible_options.to_csv(
    diagnostics_dir / "modern_2024_c_j_eligible_options.csv",
    index=False,
)

preference_comparison.to_csv(
    diagnostics_dir / "modern_2024_c_j_preference_comparison.csv",
    index=False,
)

scenario_parameters = pd.DataFrame([
    {
        "scenario": scenario,
        "survival_weight": survival_weight,
        "high_growth_weight": 1 - survival_weight,
        "minimum_survival_3y": minimum_survival,
        "reference_year": 2024,
        "reference_n": len(modern_2024_common),
    }
    for scenario, survival_weight in scenarios.items()
])

scenario_parameters.to_csv(
    diagnostics_dir / "modern_2024_c_j_scenario_parameters.csv",
    index=False,
)
# %%
