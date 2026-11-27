# %%
from pathlib import Path

import numpy as np
import pandas as pd


# 1. Загрузка и подготовка общей выборки

project_root = Path(__file__).resolve().parents[1]

bdi_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

components = [
    "birth_rate",
    "survival_3y",
    "high_growth_share",
]

keys = ["geo", "nace_r2", "year"]

sample = bdi_panel[keys + components].dropna().copy()

print("Complete observations:", len(sample))
print("Duplicate keys:", sample.duplicated(keys).sum())

invalid_mask = (
    ~np.isfinite(sample[components]).all(axis=1)
    | sample[components].lt(0).any(axis=1)
    | sample[components].gt(100).any(axis=1)
)

if sample.duplicated(keys).any():
    raise ValueError("Duplicate country-industry-year keys.")

if invalid_mask.any():
    print(sample.loc[invalid_mask].to_string(index=False))
    raise ValueError("Invalid component values.")


# 2. Фиксированные параметры нормализации
# Все компоненты положительно направлены.
# Наблюдаемые минимумы -> 70, максимумы -> 130.

lower_bounds = sample[components].min()
upper_bounds = sample[components].max()
component_ranges = upper_bounds - lower_bounds

if (component_ranges <= 0).any():
    raise ValueError("A component has a zero or negative range.")

normalization_parameters = pd.DataFrame({
    "lower_bound": lower_bounds,
    "upper_bound": upper_bounds,
    "range": component_ranges,
    "direction": 1,
    "reference_n": len(sample),
    "reference_start_year": int(sample["year"].min()),
    "reference_end_year": int(sample["year"].max()),
})
normalization_parameters.index.name = "component"

normalized = (
    70
    + 60
    * (sample[components] - lower_bounds)
    / component_ranges
)

for component in components:
    sample[f"normalized_{component}"] = normalized[component]


# 3. Средний уровень, несбалансированность и AMPI
# Стандартное отклонение считается между компонентами одной строки.

sample["mean_score"] = normalized.mean(axis=1)
sample["component_std"] = normalized.std(axis=1, ddof=0)

sample["imbalance_cv"] = (
    sample["component_std"] / sample["mean_score"]
)

sample["penalty"] = (
    sample["component_std"] ** 2 / sample["mean_score"]
)

sample["ampi_score"] = (
    sample["mean_score"] - sample["penalty"]
)

sample["penalty_pct_of_mean"] = (
    100 * sample["penalty"] / sample["mean_score"]
)


# 4. Ранги: эффект именно штрафа, без смены нормализации
# Положительный rank_change означает ухудшение позиции после штрафа.

sample["rank_mean"] = sample["mean_score"].rank(
    ascending=False,
    method="average",
)

sample["rank_ampi"] = sample["ampi_score"].rank(
    ascending=False,
    method="average",
)

sample["rank_change"] = (
    sample["rank_ampi"] - sample["rank_mean"]
)

sample["abs_rank_change"] = sample["rank_change"].abs()


# 5. Дополнительное сравнение с трехкомпонентным z-score индексом
# Здесь одновременно меняются нормализация и агрегирование.

reference_means = sample[components].mean()
reference_stds = sample[components].std(ddof=0)

if (reference_stds <= 0).any():
    raise ValueError("A component has a zero standard deviation.")

z_scores = (
    sample[components] - reference_means
) / reference_stds

sample["bdi_three_component_z"] = z_scores.mean(axis=1)

z_parameters = pd.DataFrame({
    "mean": reference_means,
    "std": reference_stds,
    "reference_n": len(sample),
})
z_parameters.index.name = "component"

score_correlations = sample[
    ["bdi_three_component_z", "mean_score", "ampi_score"]
].corr(method="spearman")


# 6. Проверка локальной монотонности
# Производная AMPI по каждому нормированному компоненту.
# Отрицательное значение означает нежелательное поведение:
# увеличение компонента способно уменьшить индекс.

number_of_components = len(components)
mean_score = sample["mean_score"]
component_variance = sample["component_std"] ** 2

derivatives = pd.DataFrame(index=sample.index)

for component in components:
    derivatives[component] = (
        3
        - 2 * normalized[component] / mean_score
        + component_variance / mean_score ** 2
    ) / number_of_components

monotonicity_summary = pd.DataFrame({
    "min_local_derivative": derivatives.min(),
    "nonpositive_derivative_count": (
        derivatives <= 0
    ).sum(),
})
monotonicity_summary.index.name = "component"

sample["min_local_derivative"] = derivatives.min(axis=1)


# 7. Таблицы наиболее показательных случаев

case_columns = (
    keys
    + components
    + [
        "normalized_birth_rate",
        "normalized_survival_3y",
        "normalized_high_growth_share",
        "mean_score",
        "component_std",
        "penalty",
        "ampi_score",
        "rank_mean",
        "rank_ampi",
        "rank_change",
    ]
)

largest_penalties = sample.nlargest(
    10, "penalty"
)[case_columns].copy()

largest_rank_changes = sample.nlargest(
    10, "abs_rank_change"
)[case_columns].copy()

rank_shift_summary = sample[
    ["rank_change", "abs_rank_change"]
].describe(percentiles=[0.5, 0.9, 0.95])

score_summary = sample[
    [
        "mean_score",
        "component_std",
        "penalty",
        "penalty_pct_of_mean",
        "ampi_score",
    ]
].describe(percentiles=[0.5, 0.9, 0.95])


# 8. Динамика: изменение уровня и изменение штрафа
# Это средние баллы наблюдений, не AMPI национальных агрегатов.

year_summary = (
    sample.groupby("year")
    .agg(
        n_observations=("ampi_score", "count"),
        mean_level=("mean_score", "mean"),
        mean_penalty=("penalty", "mean"),
        mean_ampi=("ampi_score", "mean"),
    )
    .reset_index()
)

year_summary["change_in_mean_level"] = (
    year_summary["mean_level"].diff()
)
year_summary["change_in_mean_penalty"] = (
    year_summary["mean_penalty"].diff()
)
year_summary["change_in_mean_ampi"] = (
    year_summary["mean_ampi"].diff()
)


# 9. Сохранение в отдельную папку эксперимента

experiment_dir = (
    project_root / "outputs/diagnostics/bdi_ampi_experiment"
)
experiment_dir.mkdir(parents=True, exist_ok=True)

tables = {
    "normalization_parameters": (
        normalization_parameters, True
    ),
    "zscore_reference_parameters": (z_parameters, True),
    "observation_comparison": (sample, False),
    "score_spearman": (score_correlations, True),
    "score_summary": (score_summary, True),
    "rank_shift_summary": (rank_shift_summary, True),
    "largest_penalties": (largest_penalties, False),
    "largest_rank_changes": (largest_rank_changes, False),
    "monotonicity_summary": (monotonicity_summary, True),
    "year_summary": (year_summary, False),
}

for filename, (table, save_index) in tables.items():
    table.to_csv(
        experiment_dir / f"{filename}.csv",
        index=save_index,
    )


# 10. Вывод результатов

print("\nNORMALIZATION PARAMETERS")
print(normalization_parameters.to_string())

print("\nSCORE SUMMARY")
print(score_summary.round(4).to_string())

print("\nSPEARMAN CORRELATIONS")
print(score_correlations.round(4).to_string())

print("\nRANK SHIFTS")
print(rank_shift_summary.round(2).to_string())

print("\nMONOTONICITY")
print(monotonicity_summary.round(6).to_string())

print("\nLARGEST PENALTIES")
print(largest_penalties.round(3).to_string(index=False))

print("\nLARGEST RANK CHANGES")
print(largest_rank_changes.round(3).to_string(index=False))

print("\nYEAR SUMMARY")
print(year_summary.round(4).to_string(index=False))

print("\nExperiment saved:", experiment_dir)
# %%
# 11. AMPI с центрированием на исторических средних
# Параметры фиксированы для всего периода 2013–2020.

centered_normalized = (
    100
    + 60
    * (sample[components] - reference_means)
    / component_ranges
)

if (centered_normalized <= 0).any().any():
    raise ValueError(
        "Nonpositive normalized values in the centered variant."
    )

for component in components:
    sample[f"centered_{component}"] = centered_normalized[component]

sample["centered_mean_score"] = centered_normalized.mean(axis=1)

sample["centered_component_std"] = centered_normalized.std(
    axis=1,
    ddof=0,
)

sample["centered_penalty"] = (
    sample["centered_component_std"] ** 2
    / sample["centered_mean_score"]
)

sample["centered_ampi_score"] = (
    sample["centered_mean_score"]
    - sample["centered_penalty"]
)


# 12. Проверка монотонности нового варианта

centered_derivatives = pd.DataFrame(index=sample.index)

for component in components:
    centered_derivatives[component] = (
        3
        - 2
        * centered_normalized[component]
        / sample["centered_mean_score"]
        + sample["centered_component_std"] ** 2
        / sample["centered_mean_score"] ** 2
    ) / number_of_components

centered_monotonicity = pd.DataFrame({
    "min_local_derivative": centered_derivatives.min(),
    "nonpositive_derivative_count": (
        centered_derivatives <= 0
    ).sum(),
})
centered_monotonicity.index.name = "component"


# 13. Сравнение рангов двух вариантов нормализации

sample["rank_centered_mean"] = (
    sample["centered_mean_score"].rank(
        ascending=False,
        method="average",
    )
)

sample["rank_centered_ampi"] = (
    sample["centered_ampi_score"].rank(
        ascending=False,
        method="average",
    )
)

# Изменение ранга из-за штрафа внутри центрированного варианта.
sample["centered_penalty_rank_change"] = (
    sample["rank_centered_ampi"]
    - sample["rank_centered_mean"]
)

sample["centered_penalty_abs_rank_change"] = (
    sample["centered_penalty_rank_change"].abs()
)

# Разница между двумя AMPI из-за выбора нормализации.
sample["normalization_abs_rank_change"] = (
    sample["rank_centered_ampi"] - sample["rank_ampi"]
).abs()

normalization_correlations = sample[
    [
        "bdi_three_component_z",
        "mean_score",
        "ampi_score",
        "centered_mean_score",
        "centered_ampi_score",
    ]
].corr(method="spearman")

normalization_rank_summary = sample[
    [
        "centered_penalty_abs_rank_change",
        "normalization_abs_rank_change",
    ]
].describe(percentiles=[0.5, 0.9, 0.95])


# 14. Параметры и диагностические таблицы

centered_parameters = pd.DataFrame({
    "reference_mean": reference_means,
    "fixed_range": component_ranges,
    "scale_multiplier": 60,
    "reference_score": 100,
    "reference_n": len(sample),
    "reference_start_year": int(sample["year"].min()),
    "reference_end_year": int(sample["year"].max()),
})
centered_parameters.index.name = "component"

centered_scale_summary = centered_normalized.agg(
    ["min", "mean", "max"]
).T

centered_score_summary = sample[
    [
        "centered_mean_score",
        "centered_component_std",
        "centered_penalty",
        "centered_ampi_score",
    ]
].describe(percentiles=[0.5, 0.9, 0.95])

centered_case_columns = (
    keys
    + components
    + [f"centered_{component}" for component in components]
    + [
        "centered_mean_score",
        "centered_penalty",
        "centered_ampi_score",
        "rank_centered_mean",
        "rank_centered_ampi",
        "centered_penalty_rank_change",
    ]
)

centered_largest_penalties = sample.nlargest(
    10, "centered_penalty"
)[centered_case_columns].copy()


# 15. Сохранение второго эксперимента

centered_tables = {
    "centered_normalization_parameters": (
        centered_parameters, True
    ),
    "centered_scale_summary": (centered_scale_summary, True),
    "centered_score_summary": (centered_score_summary, True),
    "centered_monotonicity": (centered_monotonicity, True),
    "normalization_comparison_spearman": (
        normalization_correlations, True
    ),
    "normalization_rank_summary": (
        normalization_rank_summary, True
    ),
    "centered_largest_penalties": (
        centered_largest_penalties, False
    ),
    "normalization_observation_comparison": (sample, False),
}

for filename, (table, save_index) in centered_tables.items():
    table.to_csv(
        experiment_dir / f"{filename}.csv",
        index=save_index,
    )


# 16. Вывод

print("\nCENTERED SCALE")
print(centered_scale_summary.round(4).to_string())

print("\nCENTERED SCORE SUMMARY")
print(centered_score_summary.round(4).to_string())

print("\nCENTERED MONOTONICITY")
print(centered_monotonicity.round(6).to_string())

print("\nNORMALIZATION COMPARISON")
print(normalization_correlations.round(4).to_string())

print("\nNORMALIZATION RANK SHIFTS")
print(normalization_rank_summary.round(2).to_string())

print("\nCENTERED LARGEST PENALTIES")
print(
    centered_largest_penalties.round(3).to_string(index=False)
)
# %%
# 17. Чувствительность центрированного AMPI к опорным выбросам

reference_exclusion_mask = (
    (
        (sample["geo"] == "PT")
        & (sample["nace_r2"] == "D")
        & (sample["year"] == 2016)
    )
    | (
        (sample["geo"] == "NO")
        & (sample["nace_r2"] == "D")
        & (sample["year"] == 2020)
    )
)

sensitivity_reference = sample.loc[
    ~reference_exclusion_mask
].copy()

sensitivity_means = sensitivity_reference[components].mean()

sensitivity_ranges = (
    sensitivity_reference[components].max()
    - sensitivity_reference[components].min()
)

if (sensitivity_ranges <= 0).any():
    raise ValueError("Nonpositive sensitivity normalization range.")

sensitivity_normalized = (
    100
    + 60
    * (sample[components] - sensitivity_means)
    / sensitivity_ranges
)

if (
    ~np.isfinite(sensitivity_normalized).all().all()
    or (sensitivity_normalized <= 0).any().any()
):
    raise ValueError("Invalid sensitivity normalized values.")


# 18. Средний уровень, штраф и итоговая оценка

sample["sensitivity_mean"] = sensitivity_normalized.mean(axis=1)

sample["sensitivity_std"] = sensitivity_normalized.std(
    axis=1,
    ddof=0,
)

sample["sensitivity_penalty"] = (
    sample["sensitivity_std"] ** 2
    / sample["sensitivity_mean"]
)

sample["sensitivity_ampi"] = (
    sample["sensitivity_mean"]
    - sample["sensitivity_penalty"]
)

sample["rank_sensitivity_ampi"] = (
    sample["sensitivity_ampi"].rank(
        ascending=False,
        method="average",
    )
)

sample["sensitivity_abs_rank_shift"] = (
    sample["rank_sensitivity_ampi"]
    - sample["rank_centered_ampi"]
).abs()


# 19. Проверка монотонности на всех оцениваемых наблюдениях

sensitivity_derivatives = pd.DataFrame(index=sample.index)

for component in components:
    sensitivity_derivatives[component] = (
        3
        - 2
        * sensitivity_normalized[component]
        / sample["sensitivity_mean"]
        + sample["sensitivity_std"] ** 2
        / sample["sensitivity_mean"] ** 2
    ) / number_of_components

sensitivity_monotonicity = pd.DataFrame({
    "min_local_derivative": sensitivity_derivatives.min(),
    "nonpositive_derivative_count": (
        sensitivity_derivatives <= 0
    ).sum(),
})
sensitivity_monotonicity.index.name = "component"


# 20. Сравнение параметров и результатов

sensitivity_parameters = pd.DataFrame({
    "original_reference_mean": reference_means,
    "sensitivity_reference_mean": sensitivity_means,
    "original_range": component_ranges,
    "sensitivity_range": sensitivity_ranges,
    "original_reference_n": len(sample),
    "sensitivity_reference_n": len(sensitivity_reference),
})
sensitivity_parameters.index.name = "component"

sensitivity_scale = sensitivity_normalized.agg(
    ["min", "mean", "max"]
).T

sensitivity_correlation = sample[
    ["centered_ampi_score", "sensitivity_ampi"]
].corr(method="spearman")

sensitivity_rank_summary = sample[
    ["sensitivity_abs_rank_shift"]
].describe(percentiles=[0.5, 0.9, 0.95])

sensitivity_columns = (
    keys
    + components
    + [
        "centered_penalty",
        "sensitivity_penalty",
        "centered_ampi_score",
        "sensitivity_ampi",
        "rank_centered_ampi",
        "rank_sensitivity_ampi",
        "sensitivity_abs_rank_shift",
    ]
)

sensitivity_largest_shifts = sample.nlargest(
    10, "sensitivity_abs_rank_shift"
)[sensitivity_columns].copy()


# 21. Сохранение результатов проверки

sensitivity_tables = {
    "sensitivity_parameters": (sensitivity_parameters, True),
    "sensitivity_scale": (sensitivity_scale, True),
    "sensitivity_spearman": (sensitivity_correlation, True),
    "sensitivity_rank_summary": (sensitivity_rank_summary, True),
    "sensitivity_monotonicity": (sensitivity_monotonicity, True),
    "sensitivity_largest_shifts": (
        sensitivity_largest_shifts, False
    ),
    "sensitivity_observation_comparison": (
        sample[sensitivity_columns], False
    ),
}

for filename, (table, save_index) in sensitivity_tables.items():
    table.to_csv(
        experiment_dir / f"{filename}.csv",
        index=save_index,
    )

print("\nSENSITIVITY REFERENCE SIZE")
print(len(sensitivity_reference))

print("\nSENSITIVITY PARAMETERS")
print(sensitivity_parameters.round(4).to_string())

print("\nSENSITIVITY SCALE")
print(sensitivity_scale.round(4).to_string())

print("\nSENSITIVITY SPEARMAN")
print(sensitivity_correlation.round(4).to_string())

print("\nSENSITIVITY RANK SHIFTS")
print(sensitivity_rank_summary.round(2).to_string())

print("\nSENSITIVITY MONOTONICITY")
print(sensitivity_monotonicity.round(6).to_string())

print("\nSENSITIVITY LARGEST SHIFTS")
print(
    sensitivity_largest_shifts.round(3).to_string(index=False)
)
# %%
nonmonotonic_mask = (
    sensitivity_derivatives <= 0
).any(axis=1)

print(
    sample.loc[
        nonmonotonic_mask,
        keys + components + [
            "sensitivity_mean",
            "sensitivity_penalty",
            "sensitivity_ampi",
        ],
    ].to_string(index=False)
)
# %%
# 27. Фиксированная историческая стандартизация
# reference_means и reference_stds рассчитаны выше
# на общей выборке трех компонентов.

fixed_standardized = (
    100
    + 10
    * (sample[components] - reference_means)
    / reference_stds
)

if (
    not np.isfinite(fixed_standardized.to_numpy()).all()
    or (fixed_standardized <= 0).any().any()
):
    raise ValueError(
        "Invalid normalized values in fixed-standardization experiment."
    )

for component in components:
    sample[f"fixed_standardized_{component}"] = (
        fixed_standardized[component]
    )


# 28. Средний уровень, штраф и итог

sample["fixed_mpi_mean"] = fixed_standardized.mean(axis=1)

sample["fixed_mpi_std"] = fixed_standardized.std(
    axis=1,
    ddof=0,
)

sample["fixed_mpi_penalty"] = (
    sample["fixed_mpi_std"] ** 2
    / sample["fixed_mpi_mean"]
)

sample["fixed_mpi_score"] = (
    sample["fixed_mpi_mean"]
    - sample["fixed_mpi_penalty"]
)

sample["fixed_mpi_penalty_pct"] = (
    100
    * sample["fixed_mpi_penalty"]
    / sample["fixed_mpi_mean"]
)


# 29. Монотонность при фиксированной нормализации

fixed_mpi_derivatives = pd.DataFrame(index=sample.index)

for component in components:
    fixed_mpi_derivatives[component] = (
        3
        - 2
        * fixed_standardized[component]
        / sample["fixed_mpi_mean"]
        + sample["fixed_mpi_std"] ** 2
        / sample["fixed_mpi_mean"] ** 2
    ) / number_of_components

fixed_mpi_monotonicity = pd.DataFrame({
    "min_local_derivative": fixed_mpi_derivatives.min(),
    "nonpositive_derivative_count": (
        fixed_mpi_derivatives <= 0
    ).sum(),
})
fixed_mpi_monotonicity.index.name = "component"

fixed_mpi_nonmonotonic_mask = (
    fixed_mpi_derivatives <= 0
).any(axis=1)


# 30. Ранги: сравниваем среднее и штраф на одной шкале

sample["rank_fixed_mpi_mean"] = sample["fixed_mpi_mean"].rank(
    ascending=False,
    method="average",
)

sample["rank_fixed_mpi"] = sample["fixed_mpi_score"].rank(
    ascending=False,
    method="average",
)

sample["fixed_mpi_rank_change"] = (
    sample["rank_fixed_mpi"]
    - sample["rank_fixed_mpi_mean"]
)

sample["fixed_mpi_abs_rank_change"] = (
    sample["fixed_mpi_rank_change"].abs()
)

fixed_mpi_correlations = sample[
    [
        "bdi_three_component_z",
        "centered_ampi_score",
        "fixed_mpi_mean",
        "fixed_mpi_score",
    ]
].corr(method="spearman")

fixed_mpi_rank_summary = sample[
    ["fixed_mpi_rank_change", "fixed_mpi_abs_rank_change"]
].describe(percentiles=[0.5, 0.9, 0.95])

fixed_mpi_score_summary = sample[
    [
        "fixed_mpi_mean",
        "fixed_mpi_std",
        "fixed_mpi_penalty",
        "fixed_mpi_penalty_pct",
        "fixed_mpi_score",
    ]
].describe(percentiles=[0.5, 0.9, 0.95])

fixed_mpi_scale_summary = fixed_standardized.agg(
    ["min", "mean", "max"]
).T


# 31. Характерные случаи

fixed_mpi_case_columns = (
    keys
    + components
    + [
        f"fixed_standardized_{component}"
        for component in components
    ]
    + [
        "fixed_mpi_mean",
        "fixed_mpi_penalty",
        "fixed_mpi_score",
        "rank_fixed_mpi_mean",
        "rank_fixed_mpi",
        "fixed_mpi_rank_change",
    ]
)

fixed_mpi_largest_penalties = sample.nlargest(
    10, "fixed_mpi_penalty"
)[fixed_mpi_case_columns].copy()

fixed_mpi_largest_rank_changes = sample.nlargest(
    10, "fixed_mpi_abs_rank_change"
)[fixed_mpi_case_columns].copy()

fixed_mpi_nonmonotonic_cases = sample.loc[
    fixed_mpi_nonmonotonic_mask,
    fixed_mpi_case_columns,
].copy()


# 32. Фиксируем параметры эксперимента

fixed_mpi_parameters = pd.DataFrame({
    "reference_mean": reference_means,
    "reference_std_ddof0": reference_stds,
    "normalized_reference": 100,
    "normalized_std_multiplier": 10,
    "reference_n": len(sample),
    "reference_start_year": int(sample["year"].min()),
    "reference_end_year": int(sample["year"].max()),
})
fixed_mpi_parameters.index.name = "component"


# 33. Сохранение отдельных результатов

fixed_mpi_tables = {
    "fixed_mpi_parameters": (fixed_mpi_parameters, True),
    "fixed_mpi_scale": (fixed_mpi_scale_summary, True),
    "fixed_mpi_score_summary": (fixed_mpi_score_summary, True),
    "fixed_mpi_spearman": (fixed_mpi_correlations, True),
    "fixed_mpi_rank_summary": (fixed_mpi_rank_summary, True),
    "fixed_mpi_monotonicity": (fixed_mpi_monotonicity, True),
    "fixed_mpi_nonmonotonic_cases": (
        fixed_mpi_nonmonotonic_cases, False
    ),
    "fixed_mpi_largest_penalties": (
        fixed_mpi_largest_penalties, False
    ),
    "fixed_mpi_largest_rank_changes": (
        fixed_mpi_largest_rank_changes, False
    ),
    "fixed_mpi_observation_comparison": (
        sample[
            fixed_mpi_case_columns
            + ["fixed_mpi_abs_rank_change"]
        ],
        False,
    ),
}

for filename, (table, save_index) in fixed_mpi_tables.items():
    table.to_csv(
        experiment_dir / f"{filename}.csv",
        index=save_index,
    )


# 34. Вывод

print("\nFIXED MPI SCALE")
print(fixed_mpi_scale_summary.round(4).to_string())

print("\nFIXED MPI SCORE SUMMARY")
print(fixed_mpi_score_summary.round(4).to_string())

print("\nFIXED MPI SPEARMAN")
print(fixed_mpi_correlations.round(4).to_string())

print("\nFIXED MPI RANK SHIFTS")
print(fixed_mpi_rank_summary.round(2).to_string())

print("\nFIXED MPI MONOTONICITY")
print(fixed_mpi_monotonicity.round(6).to_string())

print("\nFIXED MPI NONMONOTONIC CASES")
print(
    fixed_mpi_nonmonotonic_cases.round(3).to_string(index=False)
)

print("\nFIXED MPI LARGEST PENALTIES")
print(
    fixed_mpi_largest_penalties.round(3).to_string(index=False)
)

print("\nFIXED MPI LARGEST RANK CHANGES")
print(
    fixed_mpi_largest_rank_changes.round(3).to_string(index=False)
)
# %%
# Чувствительность MPI к исключению PT/D/2016

no_case = (
    (sample["geo"] == "NO")
    & (sample["nace_r2"] == "D")
    & (sample["year"] == 2020)
)

pt_case = (
    (sample["geo"] == "PT")
    & (sample["nace_r2"] == "D")
    & (sample["year"] == 2016)
)

reference_a = sample.loc[~no_case].copy()
reference_b = sample.loc[~(no_case | pt_case)].copy()

evaluation_sample = reference_b[
    keys + components
].copy()

experiment_results = {}
parameter_tables = []
monotonicity_tables = []

for label, reference in {
    "a_without_no": reference_a,
    "b_without_no_pt": reference_b,
}.items():
    means = reference[components].mean()
    stds = reference[components].std(ddof=0)

    if (stds <= 0).any():
        raise ValueError("Nonpositive standard deviation.")

    normalized_values = (
        100
        + 10
        * (evaluation_sample[components] - means)
        / stds
    )

    if (
        not np.isfinite(normalized_values.to_numpy()).all()
        or (normalized_values <= 0).any().any()
    ):
        raise ValueError("Invalid normalized values.")

    level = normalized_values.mean(axis=1)
    variance = normalized_values.var(axis=1, ddof=0)
    penalty = variance / level
    score = level - penalty

    evaluation_sample[f"{label}_mean"] = level
    evaluation_sample[f"{label}_penalty"] = penalty
    evaluation_sample[f"{label}_score"] = score
    evaluation_sample[f"{label}_rank"] = score.rank(
        ascending=False,
        method="average",
    )

    derivatives = pd.DataFrame({
        component: (
            3
            - 2 * normalized_values[component] / level
            + variance / level ** 2
        ) / len(components)
        for component in components
    })

    monotonicity = pd.DataFrame({
        "scenario": label,
        "min_derivative": derivatives.min(),
        "nonpositive_count": (derivatives <= 0).sum(),
    })
    monotonicity.index.name = "component"
    monotonicity_tables.append(monotonicity.reset_index())

    parameters = pd.DataFrame({
        "scenario": label,
        "reference_mean": means,
        "reference_std": stds,
        "reference_n": len(reference),
    })
    parameters.index.name = "component"
    parameter_tables.append(parameters.reset_index())

    experiment_results[label] = {
        "reference_n": len(reference),
        "evaluation_n": len(evaluation_sample),
        "mean_penalty": penalty.mean(),
        "max_penalty": penalty.max(),
        "nonmonotonic_rows": int(
            (derivatives <= 0).any(axis=1).sum()
        ),
    }

evaluation_sample["abs_rank_shift"] = (
    evaluation_sample["a_without_no_rank"]
    - evaluation_sample["b_without_no_pt_rank"]
).abs()

comparison_spearman = evaluation_sample[
    ["a_without_no_score", "b_without_no_pt_score"]
].corr(method="spearman")

comparison_rank_summary = evaluation_sample[
    ["abs_rank_shift"]
].describe(percentiles=[0.5, 0.9, 0.95])

comparison_summary = pd.DataFrame.from_dict(
    experiment_results,
    orient="index",
)
comparison_summary.index.name = "scenario"

comparison_monotonicity = pd.concat(
    monotonicity_tables,
    ignore_index=True,
)

comparison_parameters = pd.concat(
    parameter_tables,
    ignore_index=True,
)

largest_changes = evaluation_sample.nlargest(
    10, "abs_rank_shift"
).copy()

comparison_dir = experiment_dir / "exclude_no_pt"
comparison_dir.mkdir(parents=True, exist_ok=True)

evaluation_sample.to_csv(
    comparison_dir / "observation_comparison.csv",
    index=False,
)
comparison_parameters.to_csv(
    comparison_dir / "parameters.csv",
    index=False,
)
comparison_monotonicity.to_csv(
    comparison_dir / "monotonicity.csv",
    index=False,
)
comparison_summary.to_csv(
    comparison_dir / "summary.csv",
)
comparison_spearman.to_csv(
    comparison_dir / "spearman.csv",
)
comparison_rank_summary.to_csv(
    comparison_dir / "rank_shift_summary.csv",
)
largest_changes.to_csv(
    comparison_dir / "largest_rank_changes.csv",
    index=False,
)

print("\nEXCLUSION EXPERIMENT SUMMARY")
print(comparison_summary.round(4).to_string())

print("\nEXCLUSION EXPERIMENT MONOTONICITY")
print(comparison_monotonicity.round(6).to_string(index=False))

print("\nEXCLUSION EXPERIMENT SPEARMAN")
print(comparison_spearman.round(6).to_string())

print("\nEXCLUSION EXPERIMENT RANK SHIFTS")
print(comparison_rank_summary.round(2).to_string())

print("\nEXCLUSION EXPERIMENT LARGEST CHANGES")
print(largest_changes.round(3).to_string(index=False))
# %%
# Аудит винзоризации: исключаем только NO/D/2020

winsor_no_mask = (
    (sample["geo"] == "NO")
    & (sample["nace_r2"] == "D")
    & (sample["year"] == 2020)
)

winsor_sample = sample.loc[
    ~winsor_no_mask,
    keys + components,
].copy()

# Фиксированные пороги общей исторической выборки.
winsor_lower = winsor_sample[components].quantile(0.01)
winsor_upper = winsor_sample[components].quantile(0.99)

winsor_thresholds = pd.DataFrame({
    "lower_quantile": 0.01,
    "upper_quantile": 0.99,
    "lower_threshold": winsor_lower,
    "upper_threshold": winsor_upper,
    "reference_n": len(winsor_sample),
})
winsor_thresholds.index.name = "component"

change_tables = []

for component in components:
    original = winsor_sample[component]

    analytical = original.clip(
        lower=winsor_lower[component],
        upper=winsor_upper[component],
    )

    # Исходный столбец сохраняется.
    winsor_sample[f"winsor_{component}"] = analytical

    changed_mask = analytical.ne(original)

    changes = winsor_sample.loc[
        changed_mask,
        keys,
    ].copy()

    changes["component"] = component
    changes["original_value"] = original.loc[changed_mask]
    changes["analytical_value"] = analytical.loc[changed_mask]
    changes["tail"] = np.where(
        changes["original_value"] < winsor_lower[component],
        "lower",
        "upper",
    )

    change_tables.append(changes)

winsor_changes = pd.concat(
    change_tables,
    ignore_index=True,
)

winsor_change_summary = (
    winsor_changes.groupby(["component", "tail"])
    .size()
    .unstack(fill_value=0)
    .reindex(
        index=components,
        columns=["lower", "upper"],
        fill_value=0,
    )
)

winsor_change_summary["total_changed_values"] = (
    winsor_change_summary["lower"]
    + winsor_change_summary["upper"]
)

winsor_change_summary["pct_of_observations"] = (
    100
    * winsor_change_summary["total_changed_values"]
    / len(winsor_sample)
)

changed_observation_count = (
    winsor_changes[keys].drop_duplicates().shape[0]
)

winsor_dir = experiment_dir / "winsorization"
winsor_dir.mkdir(parents=True, exist_ok=True)

winsor_thresholds.to_csv(
    winsor_dir / "thresholds_01_99.csv",
)
winsor_change_summary.to_csv(
    winsor_dir / "change_summary_01_99.csv",
)
winsor_changes.to_csv(
    winsor_dir / "changed_values_01_99.csv",
    index=False,
)
winsor_sample.to_csv(
    winsor_dir / "analytical_sample_01_99.csv",
    index=False,
)

print("\nWINSORIZATION SAMPLE SIZE")
print(len(winsor_sample))

print("\nWINSORIZATION THRESHOLDS")
print(winsor_thresholds.round(4).to_string())

print("\nWINSORIZATION CHANGE SUMMARY")
print(winsor_change_summary.round(2).to_string())

print("\nOBSERVATIONS WITH AT LEAST ONE CHANGED COMPONENT")
print(changed_observation_count)

print("\nWINSORIZATION CHANGED VALUES")
print(
    winsor_changes.sort_values(
        ["component", "original_value"]
    ).round(4).to_string(index=False)
)
# %%
# Сравнение трех вариантов обработки перед MPI

treatment_sample = sample.loc[
    ~(
        (sample["geo"] == "NO")
        & (sample["nace_r2"] == "D")
        & (sample["year"] == 2020)
    ),
    keys + components,
].copy()

treatment_scenarios = {
    "raw": None,
    "winsor_005": 0.005,
    "winsor_01": 0.01,
}

treatment_results = treatment_sample.copy()
treatment_summaries = []
treatment_parameters = []
treatment_monotonicity = []

for scenario, tail_probability in treatment_scenarios.items():
    original_values = treatment_sample[components]

    if tail_probability is None:
        lower = original_values.min()
        upper = original_values.max()
        analytical_values = original_values.copy()
    else:
        lower = original_values.quantile(tail_probability)
        upper = original_values.quantile(1 - tail_probability)

        analytical_values = original_values.clip(
            lower=lower,
            upper=upper,
            axis="columns",
        )

    changed = analytical_values.ne(original_values)

    means = analytical_values.mean()
    stds = analytical_values.std(ddof=0)

    if (stds <= 0).any():
        raise ValueError(f"Nonpositive std: {scenario}")

    normalized_values = (
        100 + 10 * (analytical_values - means) / stds
    )

    if (
        not np.isfinite(normalized_values.to_numpy()).all()
        or (normalized_values <= 0).any().any()
    ):
        raise ValueError(f"Invalid normalized values: {scenario}")

    level = normalized_values.mean(axis=1)
    variance = normalized_values.var(axis=1, ddof=0)
    penalty = variance / level
    score = level - penalty

    rank_mean = level.rank(
        ascending=False, method="average"
    )
    rank_score = score.rank(
        ascending=False, method="average"
    )

    derivatives = pd.DataFrame({
        component: (
            3
            - 2 * normalized_values[component] / level
            + variance / level ** 2
        ) / len(components)
        for component in components
    })

    treatment_results[f"{scenario}_mean"] = level
    treatment_results[f"{scenario}_penalty"] = penalty
    treatment_results[f"{scenario}_score"] = score
    treatment_results[f"{scenario}_rank"] = rank_score

    for component in components:
        treatment_results[
            f"{scenario}_analytical_{component}"
        ] = analytical_values[component]

    treatment_summaries.append({
        "scenario": scenario,
        "n_observations": len(treatment_sample),
        "changed_cells": int(changed.to_numpy().sum()),
        "changed_observations": int(changed.any(axis=1).sum()),
        "mean_penalty": penalty.mean(),
        "median_penalty": penalty.median(),
        "max_penalty": penalty.max(),
        "median_rank_shift_from_penalty": (
            rank_score - rank_mean
        ).abs().median(),
        "nonmonotonic_rows": int(
            (derivatives <= 0).any(axis=1).sum()
        ),
    })

    parameters = pd.DataFrame({
        "scenario": scenario,
        "tail_probability": (
            np.nan if tail_probability is None
            else tail_probability
        ),
        "lower_threshold": lower,
        "upper_threshold": upper,
        "reference_mean": means,
        "reference_std_ddof0": stds,
        "changed_values": changed.sum(),
        "reference_n": len(treatment_sample),
    })
    parameters.index.name = "component"
    treatment_parameters.append(parameters.reset_index())

    monotonicity = pd.DataFrame({
        "scenario": scenario,
        "min_derivative": derivatives.min(),
        "nonpositive_count": (derivatives <= 0).sum(),
    })
    monotonicity.index.name = "component"
    treatment_monotonicity.append(monotonicity.reset_index())


# Различия рангов: каждый обработанный вариант против raw

rank_shift_rows = []

for scenario in ["winsor_005", "winsor_01"]:
    shifts = (
        treatment_results[f"{scenario}_rank"]
        - treatment_results["raw_rank"]
    ).abs()

    treatment_results[f"{scenario}_abs_rank_shift_vs_raw"] = (
        shifts
    )

    rank_shift_rows.append({
        "comparison": f"{scenario}_vs_raw",
        "mean_shift": shifts.mean(),
        "median_shift": shifts.median(),
        "p90_shift": shifts.quantile(0.90),
        "p95_shift": shifts.quantile(0.95),
        "max_shift": shifts.max(),
    })

between_winsor_shifts = (
    treatment_results["winsor_005_rank"]
    - treatment_results["winsor_01_rank"]
).abs()

rank_shift_rows.append({
    "comparison": "winsor_005_vs_winsor_01",
    "mean_shift": between_winsor_shifts.mean(),
    "median_shift": between_winsor_shifts.median(),
    "p90_shift": between_winsor_shifts.quantile(0.90),
    "p95_shift": between_winsor_shifts.quantile(0.95),
    "max_shift": between_winsor_shifts.max(),
})

treatment_summary = pd.DataFrame(treatment_summaries)
treatment_rank_summary = pd.DataFrame(rank_shift_rows)
treatment_parameter_table = pd.concat(
    treatment_parameters, ignore_index=True
)
treatment_monotonicity_table = pd.concat(
    treatment_monotonicity, ignore_index=True
)

treatment_correlations = treatment_results[
    [
        "raw_score",
        "winsor_005_score",
        "winsor_01_score",
    ]
].corr(method="spearman")


# Характерные случаи: PT/D/2016 и вся история PT/N

case_mask = (
    (
        (treatment_results["geo"] == "PT")
        & (treatment_results["nace_r2"] == "D")
        & (treatment_results["year"] == 2016)
    )
    | (
        (treatment_results["geo"] == "PT")
        & (treatment_results["nace_r2"] == "N")
    )
)

case_columns = keys + components

for scenario in treatment_scenarios:
    case_columns += [
        f"{scenario}_mean",
        f"{scenario}_penalty",
        f"{scenario}_score",
        f"{scenario}_rank",
    ]

treatment_cases = treatment_results.loc[
    case_mask, case_columns
].sort_values(keys)

largest_treatment_changes = treatment_results.nlargest(
    10, "winsor_01_abs_rank_shift_vs_raw"
)[
    keys
    + components
    + [
        "raw_score",
        "winsor_005_score",
        "winsor_01_score",
        "raw_rank",
        "winsor_005_rank",
        "winsor_01_rank",
        "winsor_01_abs_rank_shift_vs_raw",
    ]
].copy()


# Сохранение

treatment_dir = experiment_dir / "winsorization_comparison"
treatment_dir.mkdir(parents=True, exist_ok=True)

tables_to_save = {
    "summary": (treatment_summary, False),
    "parameters": (treatment_parameter_table, False),
    "monotonicity": (treatment_monotonicity_table, False),
    "spearman": (treatment_correlations, True),
    "rank_shifts": (treatment_rank_summary, False),
    "case_comparison": (treatment_cases, False),
    "largest_changes": (largest_treatment_changes, False),
    "observation_comparison": (treatment_results, False),
}

for filename, (table, save_index) in tables_to_save.items():
    table.to_csv(
        treatment_dir / f"{filename}.csv",
        index=save_index,
    )

print("\nTREATMENT SUMMARY")
print(treatment_summary.round(4).to_string(index=False))

print("\nTREATMENT MONOTONICITY")
print(
    treatment_monotonicity_table.round(6).to_string(index=False)
)

print("\nTREATMENT SPEARMAN")
print(treatment_correlations.round(6).to_string())

print("\nTREATMENT RANK SHIFTS")
print(treatment_rank_summary.round(2).to_string(index=False))

print("\nTREATMENT CASES")
print(treatment_cases.round(3).to_string(index=False))

print("\nTREATMENT LARGEST CHANGES")
print(
    largest_treatment_changes.round(3).to_string(index=False)
)
# %%
# Финальное сравнение заранее выбранных правил обработки

final_sample = sample.loc[
    ~(
        (sample["geo"] == "NO")
        & (sample["nace_r2"] == "D")
        & (sample["year"] == 2020)
    ),
    keys + components,
].copy()

final_rules = {
    "raw": (None, None),
    "two_sided_005": (0.005, 0.995),
    "two_sided_001": (0.001, 0.999),
    "upper_only_999": (None, 0.999),
}

final_comparison = final_sample.copy()
final_summary_rows = []
final_parameter_parts = []
final_monotonicity_parts = []
final_change_parts = []

for scenario, (lower_q, upper_q) in final_rules.items():
    original = final_sample[components]

    lower = (
        original.quantile(lower_q)
        if lower_q is not None
        else pd.Series(-np.inf, index=components)
    )
    upper = (
        original.quantile(upper_q)
        if upper_q is not None
        else pd.Series(np.inf, index=components)
    )

    analytical = original.clip(
        lower=lower,
        upper=upper,
        axis="columns",
    )
    changed = analytical.ne(original)

    means = analytical.mean()
    stds = analytical.std(ddof=0)

    if (stds <= 0).any():
        raise ValueError(f"Nonpositive standard deviation: {scenario}")

    normalized = 100 + 10 * (analytical - means) / stds

    if (
        not np.isfinite(normalized.to_numpy()).all()
        or (normalized <= 0).any().any()
    ):
        raise ValueError(f"Invalid normalized values: {scenario}")

    level = normalized.mean(axis=1)
    variance = normalized.var(axis=1, ddof=0)
    penalty = variance / level
    score = level - penalty

    final_comparison[f"{scenario}_mean"] = level
    final_comparison[f"{scenario}_penalty"] = penalty
    final_comparison[f"{scenario}_score"] = score
    final_comparison[f"{scenario}_rank"] = score.rank(
        ascending=False,
        method="average",
    )

    derivatives = pd.DataFrame({
        component: (
            3
            - 2 * normalized[component] / level
            + variance / level ** 2
        ) / len(components)
        for component in components
    })

    final_summary_rows.append({
        "scenario": scenario,
        "n_observations": len(final_sample),
        "changed_cells": int(changed.to_numpy().sum()),
        "changed_observations": int(changed.any(axis=1).sum()),
        "mean_penalty": penalty.mean(),
        "max_penalty": penalty.max(),
        "nonmonotonic_rows": int(
            (derivatives <= 0).any(axis=1).sum()
        ),
    })

    parameters = pd.DataFrame({
        "scenario": scenario,
        "lower_quantile": (
            np.nan if lower_q is None else lower_q
        ),
        "upper_quantile": (
            np.nan if upper_q is None else upper_q
        ),
        "lower_threshold": lower.replace(-np.inf, np.nan),
        "upper_threshold": upper.replace(np.inf, np.nan),
        "reference_mean": means,
        "reference_std_ddof0": stds,
        "lower_changed_count": original.lt(lower).sum(),
        "upper_changed_count": original.gt(upper).sum(),
        "reference_n": len(final_sample),
    })
    parameters.index.name = "component"
    final_parameter_parts.append(parameters.reset_index())

    monotonicity = pd.DataFrame({
        "scenario": scenario,
        "min_derivative": derivatives.min(),
        "nonpositive_count": (derivatives <= 0).sum(),
    })
    monotonicity.index.name = "component"
    final_monotonicity_parts.append(monotonicity.reset_index())

    for component in components:
        final_comparison[
            f"{scenario}_analytical_{component}"
        ] = analytical[component]

        component_changes = final_sample.loc[
            changed[component], keys
        ].copy()

        component_changes["scenario"] = scenario
        component_changes["component"] = component
        component_changes["original_value"] = original.loc[
            changed[component], component
        ]
        component_changes["analytical_value"] = analytical.loc[
            changed[component], component
        ]
        component_changes["tail"] = np.where(
            component_changes["original_value"] < lower[component],
            "lower",
            "upper",
        )
        final_change_parts.append(component_changes)


# Сравнение рангов с необработанным вариантом

final_rank_rows = []

for scenario in final_rules:
    if scenario == "raw":
        continue

    shifts = (
        final_comparison[f"{scenario}_rank"]
        - final_comparison["raw_rank"]
    ).abs()

    final_comparison[f"{scenario}_abs_shift_vs_raw"] = shifts

    final_rank_rows.append({
        "scenario": scenario,
        "mean_shift": shifts.mean(),
        "median_shift": shifts.median(),
        "p90_shift": shifts.quantile(0.90),
        "p95_shift": shifts.quantile(0.95),
        "max_shift": shifts.max(),
    })

final_summary = pd.DataFrame(final_summary_rows)
final_parameters = pd.concat(
    final_parameter_parts, ignore_index=True
)
final_monotonicity = pd.concat(
    final_monotonicity_parts, ignore_index=True
)
final_changes = pd.concat(
    final_change_parts, ignore_index=True
)
final_rank_summary = pd.DataFrame(final_rank_rows)

final_spearman = final_comparison[
    [f"{scenario}_score" for scenario in final_rules]
].corr(method="spearman")


# Характерные профили:
# PT/D/2016 — высокий birth rate;
# PT/N/2013 — низкая выживаемость;
# BE/B/2019 — высокая выживаемость.

selected_case_mask = (
    (
        (final_sample["geo"] == "PT")
        & (final_sample["nace_r2"] == "D")
        & (final_sample["year"] == 2016)
    )
    | (
        (final_sample["geo"] == "PT")
        & (final_sample["nace_r2"] == "N")
        & (final_sample["year"] == 2013)
    )
    | (
        (final_sample["geo"] == "BE")
        & (final_sample["nace_r2"] == "B")
        & (final_sample["year"] == 2019)
    )
)

final_case_parts = []

for scenario in final_rules:
    case_part = final_comparison.loc[
        selected_case_mask, keys
    ].copy()

    case_part["scenario"] = scenario

    for component in components:
        case_part[f"original_{component}"] = (
            final_comparison.loc[selected_case_mask, component]
        )
        case_part[f"analytical_{component}"] = (
            final_comparison.loc[
                selected_case_mask,
                f"{scenario}_analytical_{component}",
            ]
        )

    for metric in ["mean", "penalty", "score", "rank"]:
        case_part[metric] = final_comparison.loc[
            selected_case_mask, f"{scenario}_{metric}"
        ]

    final_case_parts.append(case_part)

final_cases = pd.concat(
    final_case_parts, ignore_index=True
).sort_values(keys + ["scenario"])


# Сохранение

final_dir = experiment_dir / "final_treatment_comparison"
final_dir.mkdir(parents=True, exist_ok=True)

final_tables = {
    "summary": (final_summary, False),
    "parameters": (final_parameters, False),
    "monotonicity": (final_monotonicity, False),
    "changed_values": (final_changes, False),
    "rank_shifts": (final_rank_summary, False),
    "spearman": (final_spearman, True),
    "case_comparison": (final_cases, False),
    "observation_comparison": (final_comparison, False),
}

for filename, (table, save_index) in final_tables.items():
    table.to_csv(
        final_dir / f"{filename}.csv",
        index=save_index,
    )

print("\nFINAL TREATMENT SUMMARY")
print(final_summary.round(4).to_string(index=False))

print("\nFINAL TREATMENT PARAMETERS")
print(final_parameters.round(4).to_string(index=False))

print("\nFINAL TREATMENT MONOTONICITY")
print(final_monotonicity.round(6).to_string(index=False))

print("\nFINAL TREATMENT SPEARMAN")
print(final_spearman.round(6).to_string())

print("\nFINAL TREATMENT RANK SHIFTS")
print(final_rank_summary.round(2).to_string(index=False))

print("\nFINAL TREATMENT CASES")
print(final_cases.round(3).to_string(index=False))
# %%
norway_d_history = bdi_panel.loc[
    (bdi_panel["geo"] == "NO")
    & (bdi_panel["nace_r2"] == "D"),
    [
        "geo",
        "nace_r2",
        "year",
        "birth_rate",
        "death_rate",
        "survival_3y",
        "high_growth_share",
    ],
].sort_values("year")

print("\nNORWAY D HISTORY")
print(norway_d_history.to_string(index=False))

norway_active_history = pd.read_csv(
    project_root
    / "outputs/diagnostics/norway_d_active_history.csv"
)

print("\nNORWAY D ACTIVE ENTERPRISES")
print(norway_active_history.to_string(index=False))
# %%
# Проверка исторических данных NO/D за 2013–2019

import sys

sys.path.insert(0, str(project_root / "src"))

from data.load_eurostat import load_eurostat_data

no_demography_source = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"
    )
)

no_demography_mask = (
    (no_demography_source["geo"] == "NO")
    & (no_demography_source["nace_r2"] == "D")
    & (no_demography_source["sizeclas"] == "TOTAL")
    & no_demography_source["year"].between(2013, 2019)
    & no_demography_source["indic_sb"].isin([
        "V11910",  # Активные предприятия
        "V11920",  # Рождения предприятий
        "V11930",  # Закрытия предприятий
        "V97020",  # Birth rate
        "V97030",  # Death rate
        "V97043",  # Трехлетняя выживаемость
    ])
)

no_demography_audit = no_demography_source.loc[
    no_demography_mask
].copy()

duplicate_count = no_demography_audit.duplicated(
    ["year", "indic_sb"]
).sum()

print("\nNO/D DEMOGRAPHY DUPLICATES")
print(duplicate_count)

if duplicate_count:
    raise ValueError("Unexpected duplicate NO/D demographic keys.")

no_demography_wide = no_demography_audit.pivot(
    index="year",
    columns="indic_sb",
    values="value",
).rename(columns={
    "V11910": "active_count",
    "V11920": "birth_count",
    "V11930": "death_count",
    "V97020": "published_birth_rate",
    "V97030": "published_death_rate",
    "V97043": "published_survival_3y",
})

no_demography_wide.columns.name = None

positive_denominator = no_demography_wide[
    "active_count"
].where(no_demography_wide["active_count"] > 0)

no_demography_wide["calculated_birth_rate"] = (
    100 * no_demography_wide["birth_count"]
    / positive_denominator
)

no_demography_wide["calculated_death_rate"] = (
    100 * no_demography_wide["death_count"]
    / positive_denominator
)

no_demography_wide["birth_abs_difference_pp"] = (
    no_demography_wide["published_birth_rate"]
    - no_demography_wide["calculated_birth_rate"]
).abs()

no_demography_wide["death_abs_difference_pp"] = (
    no_demography_wide["published_death_rate"]
    - no_demography_wide["calculated_death_rate"]
).abs()

print("\nNO/D DEMOGRAPHY RATE CHECK")
print(no_demography_wide.round(4).to_string())

print("\nNO/D DEMOGRAPHY FLAGS")
print(
    no_demography_audit[
        ["year", "indic_sb", "value_raw", "flag"]
    ]
    .sort_values(["year", "indic_sb"])
    .to_string(index=False)
)


# High-growth: сначала смотрим все имеющиеся показатели
# и измерения, чтобы правильно определить числитель и знаменатель.

no_high_growth_source = load_eurostat_data(
    str(
        project_root
        / "data/raw/bd_9pm_r2_High_growth_enterprises.tsv.gz"
    )
)

no_high_growth_audit = no_high_growth_source.loc[
    (no_high_growth_source["geo"] == "NO")
    & (no_high_growth_source["nace_r2"] == "D")
    & no_high_growth_source["year"].between(2013, 2019)
].copy()

print("\nNO/D HIGH-GROWTH SOURCE ROWS")
print(
    no_high_growth_audit
    .sort_values(["year", "indic_sb"])
    .to_string(index=False)
)


# Сохранение исходного аудита

no_audit_dir = experiment_dir / "norway_d_2013_2019_audit"
no_audit_dir.mkdir(parents=True, exist_ok=True)

no_demography_audit.to_csv(
    no_audit_dir / "demography_source_rows.csv",
    index=False,
)

no_demography_wide.to_csv(
    no_audit_dir / "demography_rate_check.csv",
    index=True,
)

no_high_growth_audit.to_csv(
    no_audit_dir / "high_growth_source_rows.csv",
    index=False,
)
# %%
no_size_mask = (
    (no_demography_source["geo"] == "NO")
    & (no_demography_source["nace_r2"] == "D")
    & no_demography_source["year"].between(2013, 2019)
    & (no_demography_source["indic_sb"] == "V11910")
)

print(
    no_demography_source.loc[
        no_size_mask, "sizeclas"
    ].drop_duplicates().to_list()
)
# %%
# Чувствительность выбранного MPI к сохранению NO/D/2013–2019

no_d_all_mask = (
    (sample["geo"] == "NO")
    & (sample["nace_r2"] == "D")
    & sample["year"].between(2013, 2020)
)

no_d_2020_mask = (
    no_d_all_mask
    & (sample["year"] == 2020)
)

no_d_main_reference = sample.loc[
    ~no_d_2020_mask, keys + components
].copy()

no_d_alternative_reference = sample.loc[
    ~no_d_all_mask, keys + components
].copy()

# Одинаковые наблюдения для сравнения результатов.
no_d_evaluation = no_d_alternative_reference.copy()

no_d_parameter_parts = []
no_d_summary_rows = []

for scenario, reference in {
    "keep_2013_2019": no_d_main_reference,
    "exclude_all_no_d": no_d_alternative_reference,
}.items():
    upper_limits = reference[components].quantile(0.999)

    treated_reference = reference[components].clip(
        upper=upper_limits,
        axis="columns",
    )

    means = treated_reference.mean()
    stds = treated_reference.std(ddof=0)

    if (stds <= 0).any():
        raise ValueError(f"Nonpositive std: {scenario}")

    treated_evaluation = no_d_evaluation[components].clip(
        upper=upper_limits,
        axis="columns",
    )

    normalized = (
        100 + 10 * (treated_evaluation - means) / stds
    )

    if (
        not np.isfinite(normalized.to_numpy()).all()
        or (normalized <= 0).any().any()
    ):
        raise ValueError(f"Invalid normalized values: {scenario}")

    level = normalized.mean(axis=1)
    variance = normalized.var(axis=1, ddof=0)
    penalty = variance / level
    score = level - penalty

    no_d_evaluation[f"{scenario}_mean"] = level
    no_d_evaluation[f"{scenario}_penalty"] = penalty
    no_d_evaluation[f"{scenario}_score"] = score
    no_d_evaluation[f"{scenario}_rank"] = score.rank(
        ascending=False,
        method="average",
    )

    derivatives = pd.DataFrame({
        component: (
            3
            - 2 * normalized[component] / level
            + variance / level ** 2
        ) / len(components)
        for component in components
    })

    no_d_summary_rows.append({
        "scenario": scenario,
        "reference_n": len(reference),
        "evaluation_n": len(no_d_evaluation),
        "mean_score": score.mean(),
        "mean_penalty": penalty.mean(),
        "nonmonotonic_rows": int(
            (derivatives <= 0).any(axis=1).sum()
        ),
    })

    parameters = pd.DataFrame({
        "scenario": scenario,
        "upper_percentile": 0.999,
        "upper_limit": upper_limits,
        "reference_mean": means,
        "reference_std_ddof0": stds,
        "reference_n": len(reference),
    })
    parameters.index.name = "component"
    no_d_parameter_parts.append(parameters.reset_index())


# Сдвиги рангов и баллов на общей выборке

no_d_evaluation["abs_rank_shift"] = (
    no_d_evaluation["keep_2013_2019_rank"]
    - no_d_evaluation["exclude_all_no_d_rank"]
).abs()

no_d_evaluation["score_difference"] = (
    no_d_evaluation["exclude_all_no_d_score"]
    - no_d_evaluation["keep_2013_2019_score"]
)

no_d_summary = pd.DataFrame(no_d_summary_rows)

no_d_parameters = pd.concat(
    no_d_parameter_parts,
    ignore_index=True,
)

no_d_spearman = no_d_evaluation[
    ["keep_2013_2019_score", "exclude_all_no_d_score"]
].corr(method="spearman")

no_d_shift_summary = no_d_evaluation[
    ["abs_rank_shift", "score_difference"]
].describe(percentiles=[0.5, 0.9, 0.95])

no_d_largest_changes = no_d_evaluation.nlargest(
    10, "abs_rank_shift"
).copy()


# Сохранение

no_d_sensitivity_dir = (
    experiment_dir / "norway_d_full_exclusion_sensitivity"
)
no_d_sensitivity_dir.mkdir(parents=True, exist_ok=True)

no_d_tables = {
    "summary": (no_d_summary, False),
    "parameters": (no_d_parameters, False),
    "spearman": (no_d_spearman, True),
    "shift_summary": (no_d_shift_summary, True),
    "largest_changes": (no_d_largest_changes, False),
    "observation_comparison": (no_d_evaluation, False),
}

for filename, (table, save_index) in no_d_tables.items():
    table.to_csv(
        no_d_sensitivity_dir / f"{filename}.csv",
        index=save_index,
    )

print("\nNO/D FULL EXCLUSION SUMMARY")
print(no_d_summary.round(6).to_string(index=False))

print("\nNO/D FULL EXCLUSION PARAMETERS")
print(no_d_parameters.round(6).to_string(index=False))

print("\nNO/D FULL EXCLUSION SPEARMAN")
print(no_d_spearman.round(6).to_string())

print("\nNO/D FULL EXCLUSION SHIFTS")
print(no_d_shift_summary.round(4).to_string())

print("\nNO/D FULL EXCLUSION LARGEST CHANGES")
print(no_d_largest_changes.round(4).to_string(index=False))
# %%
