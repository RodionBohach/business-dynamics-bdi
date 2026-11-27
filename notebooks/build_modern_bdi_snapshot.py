# %%
from pathlib import Path
import sys

import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from data.load_eurostat import load_eurostat_data

keys = ["geo", "nace_r2", "year"]

main_countries = [
    "AT", "BE", "BG", "CZ", "DE", "EE", "ES", "FI", "FR", "HU",
    "IT", "LV", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK",
]
main_nace = [
    "B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N",
]

diagnostics_dir = project_root / "outputs/diagnostics"
descriptive_dir = project_root / "outputs/descriptive"
coverage_dir = project_root / "outputs/coverage"

for directory in [
    diagnostics_dir, descriptive_dir, coverage_dir
]:
    directory.mkdir(parents=True, exist_ok=True)


# %%
# Загрузка источников

modern_horizons = pd.read_csv(
    project_root
    / "data/processed/modern_survival_growth_audited_long.csv"
)

modern_demography = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_size_total_Business_demography_by_size_class.tsv.gz"
    )
)

modern_high_growth = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_hg_High_growth_enterprises_and_related_employment.tsv.gz"
    )
)


def core_mask(data):
    return (
        data["geo"].isin(main_countries)
        & data["nace_r2"].isin(main_nace)
        & data["year"].between(2021, 2024)
    )


# %%
# Birth/death и high-growth

demography = modern_demography.loc[
    core_mask(modern_demography)
    & modern_demography["age"].eq("TOTAL")
    & modern_demography["sizeclas"].eq("TOTAL")
    & modern_demography["indic_sbs"].isin(
        ["ENT_BRTHR_PC", "ENT_DTHR_PC"]
    )
].copy()

demography["component"] = demography["indic_sbs"].map({
    "ENT_BRTHR_PC": "birth_rate",
    "ENT_DTHR_PC": "death_rate",
})

high_growth = modern_high_growth.loc[
    core_mask(modern_high_growth)
    & modern_high_growth["indic_sbs"].eq("ENT_HGRWR_PC")
].copy()

high_growth["component"] = "high_growth_share"

long_columns = keys + ["component", "value"]

common_long = pd.concat(
    [
        demography[long_columns],
        high_growth[long_columns],
    ],
    ignore_index=True,
)

if common_long.duplicated(keys + ["component"]).any():
    raise ValueError("Duplicate modern component keys.")

common_wide = common_long.pivot(
    index=keys,
    columns="component",
    values="value",
).reset_index()
common_wide.columns.name = None


# %%
# Survival: используем уже проверенные аналитические значения.

survival_long = modern_horizons.loc[
    core_mask(modern_horizons)
    & modern_horizons["component"].eq("survival_rate")
].copy()

if survival_long.duplicated(keys + ["horizon"]).any():
    raise ValueError("Duplicate modern survival keys.")

survival_wide = survival_long.pivot(
    index=keys,
    columns="horizon",
    values="value_analytical",
).reset_index().rename(columns={
    1: "survival_1y",
    2: "survival_2y",
    3: "survival_3y",
})
survival_wide.columns.name = None

modern = common_wide.merge(
    survival_wide,
    on=keys,
    how="outer",
    validate="one_to_one",
    indicator=True,
)

print("\nMODERN MPI MERGE")
print(modern["_merge"].value_counts())

if not modern["_merge"].eq("both").all():
    raise ValueError("Unmatched modern keys.")

modern = modern.drop(columns="_merge")
modern["churn"] = modern["birth_rate"] + modern["death_rate"]


# %%
# Покрытие без требования наличия death rate.

common_components = ["birth_rate", "high_growth_share"]
survival_columns = {
    1: "survival_1y",
    2: "survival_2y",
    3: "survival_3y",
}
components = common_components + list(survival_columns.values())

observed_values = modern[components].to_numpy(dtype=float)
present = ~np.isnan(observed_values)

if (
    not np.isfinite(observed_values[present]).all()
    or (observed_values[present] < 0).any()
    or (observed_values[present] > 100).any()
):
    raise ValueError("Invalid modern component values.")

for horizon, survival_column in survival_columns.items():
    modern[f"complete_s{horizon}"] = modern[
        common_components + [survival_column]
    ].notna().all(axis=1)

complete_columns = [
    "complete_s1", "complete_s2", "complete_s3"
]

coverage = modern.groupby("year")[complete_columns].sum()

common_2024_mask = (
    modern["year"].eq(2024)
    & modern[complete_columns].all(axis=1)
)

reference = modern.loc[
    common_2024_mask, components
].copy()

if reference.empty:
    raise ValueError("Empty common 2024 reference.")


# %%
# Единая современная база 2024.
# Пороги, средние и std фиксированы для всех современных лет.

upper_limits = reference.quantile(0.999)

treated_reference = reference.clip(
    upper=upper_limits,
    axis="columns",
)

means = treated_reference.mean()
stds = treated_reference.std(ddof=0)

if (stds <= 0).any():
    raise ValueError("Nonpositive modern standard deviation.")

parameters = pd.DataFrame({
    "upper_quantile": 0.999,
    "upper_threshold": upper_limits,
    "mean_after_winsorization": means,
    "std_after_winsorization_ddof0": stds,
    "normalized_reference": 100,
    "normalized_std_multiplier": 10,
    "reference_year": 2024,
    "reference_n": len(reference),
})
parameters.index.name = "component"

analytical = modern[components].clip(
    upper=upper_limits,
    axis="columns",
)

normalized = 100 + 10 * (analytical - means) / stds

for component in components:
    modern[f"mpi_analytical_{component}"] = analytical[component]
    modern[f"mpi_normalized_{component}"] = normalized[component]


# %%
# Доступные версии по годам.
# Редкое покрытие ранних лет не используем для индекса.

available_years = {
    1: [2022, 2023, 2024],
    2: [2023, 2024],
    3: [2024],
}

monotonicity_rows = []

for horizon, survival_column in survival_columns.items():
    selected = common_components + [survival_column]

    valid = (
        modern[f"complete_s{horizon}"]
        & modern["year"].isin(available_years[horizon])
    )

    scores = normalized.loc[valid, selected]

    if (
        not np.isfinite(scores.to_numpy()).all()
        or (scores <= 0).any().any()
    ):
        raise ValueError(
            f"Invalid normalized modern S{horizon} scores."
        )

    level = scores.mean(axis=1)
    variance = scores.var(axis=1, ddof=0)
    penalty = variance / level

    modern[f"mpi_s{horizon}_mean"] = np.nan
    modern[f"mpi_s{horizon}_penalty"] = np.nan
    modern[f"mpi_s{horizon}"] = np.nan

    modern.loc[valid, f"mpi_s{horizon}_mean"] = level
    modern.loc[valid, f"mpi_s{horizon}_penalty"] = penalty
    modern.loc[valid, f"mpi_s{horizon}"] = level - penalty

    for component in selected:
        derivative = (
            3
            - 2 * scores[component] / level
            + variance / level ** 2
        ) / len(selected)

        monotonicity_rows.append({
            "horizon": horizon,
            "component": component,
            "n_observations": len(scores),
            "min_local_derivative": derivative.min(),
            "nonpositive_count": int((derivative <= 0).sum()),
        })

monotonicity = pd.DataFrame(monotonicity_rows)

print("\nMODERN MPI MONOTONICITY")
print(monotonicity.round(6).to_string(index=False))

if monotonicity["nonpositive_count"].gt(0).any():
    raise ValueError(
        "Modern MPI monotonicity violation. "
        "Review before adopting these results."
    )


# %%
# Прямое сравнение горизонтов: общие наблюдения 2024.

snapshot = modern.loc[common_2024_mask].copy()

score_columns = ["mpi_s1", "mpi_s2", "mpi_s3"]
horizon_spearman = snapshot[score_columns].corr(
    method="spearman"
)

for horizon in [1, 2, 3]:
    snapshot[f"rank_s{horizon}"] = snapshot[
        f"mpi_s{horizon}"
    ].rank(ascending=False, method="average")

for horizon in [1, 2]:
    snapshot[f"rank_shift_s{horizon}_vs_s3"] = (
        snapshot[f"rank_s{horizon}"] - snapshot["rank_s3"]
    ).abs()

rank_summary = snapshot[
    ["rank_shift_s1_vs_s3", "rank_shift_s2_vs_s3"]
].describe(percentiles=[0.5, 0.9, 0.95])

country_summary = (
    snapshot.groupby("geo")
    .agg(
        n_industries=("nace_r2", "nunique"),
        birth_rate=("birth_rate", "mean"),
        death_rate=("death_rate", "mean"),
        churn=("churn", "mean"),
        high_growth_share=("high_growth_share", "mean"),
        survival_1y=("survival_1y", "mean"),
        survival_2y=("survival_2y", "mean"),
        survival_3y=("survival_3y", "mean"),
        mpi_s1=("mpi_s1", "mean"),
        mpi_s2=("mpi_s2", "mean"),
        mpi_s3=("mpi_s3", "mean"),
        mean_level_s3=("mpi_s3_mean", "mean"),
        mean_penalty_s3=("mpi_s3_penalty", "mean"),
    )
    .sort_values("mpi_s3", ascending=False)
)

excluded_2024 = modern.loc[
    modern["year"].eq(2024)
    & ~modern[complete_columns].all(axis=1),
    keys + components,
].copy()


# %%
# Постоянный состав пар внутри временного ряда каждой версии.

balanced_parts = []

for horizon, years in available_years.items():
    score_column = f"mpi_s{horizon}"

    available = modern.loc[
        modern["year"].isin(years)
        & modern[score_column].notna()
    ].copy()

    counts = available.groupby(
        ["geo", "nace_r2"]
    )["year"].nunique()

    balanced_pairs = counts.loc[counts.eq(len(years))].index

    pair_keys = pd.MultiIndex.from_frame(
        available[["geo", "nace_r2"]]
    )

    selected = available.loc[
        pair_keys.isin(balanced_pairs),
        keys + [
            score_column,
            f"mpi_s{horizon}_mean",
            f"mpi_s{horizon}_penalty",
        ],
    ].rename(columns={
        score_column: "bdi_mpi",
        f"mpi_s{horizon}_mean": "mean_level",
        f"mpi_s{horizon}_penalty": "penalty",
    })

    selected["survival_horizon"] = horizon
    balanced_parts.append(selected)

balanced = pd.concat(balanced_parts, ignore_index=True)

dynamics_summary = (
    balanced.groupby(["survival_horizon", "year"])
    .agg(
        n_observations=("bdi_mpi", "count"),
        mean_mpi=("bdi_mpi", "mean"),
        median_mpi=("bdi_mpi", "median"),
        std_mpi=("bdi_mpi", "std"),
        mean_level=("mean_level", "mean"),
        mean_penalty=("penalty", "mean"),
    )
    .reset_index()
    .sort_values(["survival_horizon", "year"])
)

for column in ["mean_mpi", "mean_level", "mean_penalty"]:
    dynamics_summary[f"change_{column}"] = (
        dynamics_summary.groupby("survival_horizon")[column]
        .diff()
    )


# %%
# Отдельные имена выходов новой конструкции.

diagnostic_tables = {
    "modern_mpi_2024_parameters": (parameters, True),
    "modern_mpi_monotonicity": (monotonicity, False),
    "modern_mpi_2024_horizon_comparison": (snapshot, False),
    "modern_mpi_2024_horizon_spearman": (horizon_spearman, True),
    "modern_mpi_2024_rank_shift_summary": (rank_summary, True),
    "modern_mpi_2024_excluded_observations": (
        excluded_2024, False
    ),
    "modern_mpi_dynamics_available": (modern, False),
    "modern_mpi_dynamics_balanced": (balanced, False),
}

for filename, (table, save_index) in diagnostic_tables.items():
    table.to_csv(
        diagnostics_dir / f"{filename}.csv",
        index=save_index,
    )

coverage.to_csv(
    coverage_dir / "modern_mpi_complete_coverage.csv"
)

country_summary.to_csv(
    descriptive_dir / "modern_mpi_2024_country_summary.csv"
)

dynamics_summary.to_csv(
    descriptive_dir / "modern_mpi_dynamics_summary.csv",
    index=False,
)

print("\nMODERN MPI COVERAGE")
print(coverage.to_string())

print("\nMODERN MPI CALCULATED COUNTS")
print(modern.groupby("year")[score_columns].count().to_string())

print("\nMODERN MPI COMMON 2024 OBSERVATIONS")
print(len(snapshot))

print("\nMODERN MPI HORIZON SPEARMAN")
print(horizon_spearman.round(6).to_string())

print("\nMODERN MPI RANK SHIFTS")
print(rank_summary.round(2).to_string())

print("\nMODERN MPI COUNTRY SUMMARY")
print(country_summary.round(4).to_string())

print("\nMODERN MPI DYNAMICS")
print(dynamics_summary.round(4).to_string(index=False))