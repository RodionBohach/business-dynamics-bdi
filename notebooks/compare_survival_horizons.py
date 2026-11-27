# %%
from pathlib import Path

import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parents[1]

bdi_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

historical_horizons = pd.read_csv(
    project_root
    / "data/processed/historical_survival_growth_audited_long.csv"
)

diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

keys = ["geo", "nace_r2", "year"]


# %%
# Исходные survival-горизонты.
# Эту таблицу также использует сохраненный ниже когортный аудит.

historical_horizons_comparison = historical_horizons.loc[
    (historical_horizons["component"] == "survival_rate")
    & historical_horizons["year"].between(2013, 2020)
].copy()

if historical_horizons_comparison.duplicated(
    keys + ["horizon"]
).any():
    raise ValueError("Duplicate historical survival keys.")

survival_wide = (
    historical_horizons_comparison.pivot(
        index=keys,
        columns="horizon",
        values="value_analytical",
    )
    .reset_index()
    .rename(columns={
        1: "survival_1y",
        2: "survival_2y",
        3: "survival_3y_new",
    })
)
survival_wide.columns.name = None

horizon_comparison = bdi_panel.merge(
    survival_wide,
    on=keys,
    how="outer",
    validate="one_to_one",
    indicator=True,
)

print("\nHORIZON MERGE")
print(horizon_comparison["_merge"].value_counts())

if not horizon_comparison["_merge"].eq("both").all():
    raise ValueError("Unmatched horizon keys.")

old_s3 = horizon_comparison["survival_3y"]
new_s3 = horizon_comparison["survival_3y_new"]

if (
    not old_s3.isna().equals(new_s3.isna())
    or not np.allclose(old_s3, new_s3, equal_nan=True)
):
    raise ValueError("Original and audited S3 do not match.")

horizon_comparison = horizon_comparison.drop(columns="_merge")


# %%
# Общая выборка трех версий; death rate не требуется.

horizon_components = [
    "birth_rate",
    "high_growth_share",
    "survival_1y",
    "survival_2y",
    "survival_3y_new",
]

quality_exclusion = (
    (horizon_comparison["geo"] == "NO")
    & (horizon_comparison["nace_r2"] == "D")
    & (horizon_comparison["year"] == 2020)
)

common_horizon_sample = (
    horizon_comparison.loc[
        ~quality_exclusion,
        keys + horizon_components,
    ]
    .dropna(subset=horizon_components)
    .copy()
)

values = common_horizon_sample[horizon_components]

if (
    values.empty
    or not np.isfinite(values.to_numpy()).all()
    or values.lt(0).any().any()
    or values.gt(100).any().any()
):
    raise ValueError("Invalid common horizon sample.")


# %%
# Обработка и фиксированные параметры на общей выборке.
# Для каждого survival-горизонта собственный порог и база.

upper_limits = values.quantile(0.999)

analytical = values.clip(
    upper=upper_limits,
    axis="columns",
)

horizon_means = analytical.mean()
horizon_stds = analytical.std(ddof=0)

if (horizon_stds <= 0).any():
    raise ValueError("Nonpositive horizon standard deviation.")

normalized = (
    100 + 10 * (analytical - horizon_means) / horizon_stds
)

if (
    not np.isfinite(normalized.to_numpy()).all()
    or (normalized <= 0).any().any()
):
    raise ValueError("Invalid horizon normalized values.")

changed = analytical.ne(values)

for component in horizon_components:
    common_horizon_sample[f"analytical_{component}"] = (
        analytical[component]
    )
    common_horizon_sample[f"normalized_{component}"] = (
        normalized[component]
    )

horizon_parameters = pd.DataFrame({
    "upper_quantile": 0.999,
    "upper_threshold": upper_limits,
    "mean_after_winsorization": horizon_means,
    "std_after_winsorization_ddof0": horizon_stds,
    "normalized_reference": 100,
    "normalized_std_multiplier": 10,
    "reference_n": len(values),
    "changed_values": changed.sum(),
})
horizon_parameters.index.name = "component"


# %%
# Три MPI с одной и той же тройкой направлений.
# Меняется только survival-горизонт.

survival_columns = {
    1: "survival_1y",
    2: "survival_2y",
    3: "survival_3y_new",
}

monotonicity_parts = []

for horizon, survival_column in survival_columns.items():
    selected_components = [
        "birth_rate",
        survival_column,
        "high_growth_share",
    ]

    scores = normalized[selected_components]
    level = scores.mean(axis=1)
    variance = scores.var(axis=1, ddof=0)
    penalty = variance / level

    common_horizon_sample[f"mpi_s{horizon}_mean"] = level
    common_horizon_sample[f"mpi_s{horizon}_penalty"] = penalty
    common_horizon_sample[f"mpi_s{horizon}"] = level - penalty

    common_horizon_sample[f"rank_s{horizon}"] = (
        common_horizon_sample[f"mpi_s{horizon}"]
        .rank(ascending=False, method="average")
    )

    for component in selected_components:
        derivative = (
            3
            - 2 * scores[component] / level
            + variance / level ** 2
        ) / len(selected_components)

        monotonicity_parts.append({
            "horizon": horizon,
            "component": component,
            "min_local_derivative": derivative.min(),
            "nonpositive_count": int((derivative <= 0).sum()),
        })

horizon_monotonicity = pd.DataFrame(monotonicity_parts)


# %%
# Сопоставление рангов и исходной выживаемости

horizon_spearman = common_horizon_sample[
    ["mpi_s1", "mpi_s2", "mpi_s3"]
].corr(method="spearman")

survival_only_spearman = common_horizon_sample[
    list(survival_columns.values())
].corr(method="spearman")

for horizon in [1, 2]:
    common_horizon_sample[f"rank_shift_s{horizon}_vs_s3"] = (
        common_horizon_sample[f"rank_s{horizon}"]
        - common_horizon_sample["rank_s3"]
    ).abs()

rank_shift_summary = common_horizon_sample[
    ["rank_shift_s1_vs_s3", "rank_shift_s2_vs_s3"]
].describe(percentiles=[0.5, 0.9, 0.95])


# %%
# Новые имена сохраняют прежние сравнения отдельно.

horizon_tables = {
    "mpi_survival_horizon_parameters": (horizon_parameters, True),
    "mpi_survival_horizon_monotonicity": (
        horizon_monotonicity, False
    ),
    "mpi_survival_horizon_spearman": (horizon_spearman, True),
    "mpi_survival_rates_horizon_spearman": (
        survival_only_spearman, True
    ),
    "mpi_survival_horizon_rank_shift_summary": (
        rank_shift_summary, True
    ),
    "mpi_survival_horizon_comparison": (
        common_horizon_sample, False
    ),
}

for filename, (table, save_index) in horizon_tables.items():
    table.to_csv(
        diagnostics_dir / f"{filename}.csv",
        index=save_index,
    )

print("\nMPI HORIZON COMMON SAMPLE")
print(len(common_horizon_sample))

print("\nMPI HORIZON MONOTONICITY")
print(horizon_monotonicity.round(6).to_string(index=False))

print("\nMPI HORIZON SPEARMAN")
print(horizon_spearman.round(6).to_string())

print("\nSURVIVAL ONLY SPEARMAN")
print(survival_only_spearman.round(6).to_string())

print("\nMPI HORIZON RANK SHIFTS")
print(rank_shift_summary.round(2).to_string())


# %%
# Ниже оставь существующий код, начиная с добавления birth_year.
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
