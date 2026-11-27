# %%
from pathlib import Path

import numpy as np
import pandas as pd


project_root = Path(__file__).resolve().parents[2]

panel = pd.read_csv(
    project_root / "data/final/analytical_panel.csv"
)

keys = ["geo", "nace_r2", "year"]

if panel.duplicated(keys).any():
    raise ValueError("Duplicate analytical-panel keys.")

bdi_panel = panel.copy()


# %%
# Прежние четырехкомпонентные индексы.
# Сохраняем их определения и параметры для сравнения.

legacy_directions = pd.Series({
    "birth_rate": 1,
    "death_rate": -1,
    "survival_3y": 1,
    "high_growth_share": 1,
})

legacy_components = legacy_directions.index.tolist()

bdi_panel["bdi_complete"] = (
    bdi_panel[legacy_components].notna().all(axis=1)
)

legacy_reference = bdi_panel.loc[
    bdi_panel["bdi_complete"],
    legacy_components,
].copy()

legacy_means = legacy_reference.mean()
legacy_stds = legacy_reference.std(ddof=0)
legacy_mins = legacy_reference.min()
legacy_maxs = legacy_reference.max()
legacy_ranges = legacy_maxs - legacy_mins

if (
    (legacy_stds <= 0).any()
    or (legacy_ranges <= 0).any()
):
    raise ValueError("Invalid legacy normalization parameters.")

legacy_z = (
    (bdi_panel[legacy_components] - legacy_means)
    / legacy_stds
) * legacy_directions

bdi_panel["bdi_zscore"] = legacy_z.mean(
    axis=1,
    skipna=False,
)

legacy_minmax = (
    bdi_panel[legacy_components] - legacy_mins
) / legacy_ranges

legacy_minmax["death_rate"] = (
    1 - legacy_minmax["death_rate"]
)

bdi_panel["bdi_minmax"] = legacy_minmax.mean(
    axis=1,
    skipna=False,
)

legacy_parameters = pd.DataFrame({
    "mean": legacy_means,
    "std": legacy_stds,
    "min": legacy_mins,
    "max": legacy_maxs,
    "direction": legacy_directions,
    "weight": 1 / len(legacy_components),
    "reference_n": len(legacy_reference),
})
legacy_parameters.index.name = "component"


# %%
# Новый основной индекс: три компонента + штраф MPI.

mpi_components = [
    "birth_rate",
    "survival_3y",
    "high_growth_share",
]

upper_quantile = 0.999
normalized_reference = 100.0
normalized_std_multiplier = 10.0

# Исключение по качеству данных.
# Исходные значения в панели не удаляются.
quality_exclusion = (
    (bdi_panel["geo"] == "NO")
    & (bdi_panel["nace_r2"] == "D")
    & (bdi_panel["year"] == 2020)
)

bdi_panel["bdi_mpi_quality_excluded"] = quality_exclusion
bdi_panel["bdi_mpi_exclusion_reason"] = ""

bdi_panel.loc[
    quality_exclusion,
    "bdi_mpi_exclusion_reason",
] = "NO/D/2020: documented historical data-quality concerns"

bdi_panel["bdi_mpi_components_complete"] = (
    bdi_panel[mpi_components].notna().all(axis=1)
)

bdi_panel["bdi_mpi_complete"] = (
    bdi_panel["bdi_mpi_components_complete"]
    & ~quality_exclusion
)

mpi_mask = bdi_panel["bdi_mpi_complete"]

mpi_reference = bdi_panel.loc[
    mpi_mask,
    mpi_components,
].copy()

if mpi_reference.empty:
    raise ValueError("Empty MPI reference sample.")

if not np.isfinite(mpi_reference.to_numpy()).all():
    raise ValueError("Non-finite MPI component values.")

if (
    mpi_reference.lt(0).any().any()
    or mpi_reference.gt(100).any().any()
):
    raise ValueError("MPI component values outside 0–100%.")


# %%
# Верхняя винзоризация.
# Низкие значения не повышаются.

mpi_upper_limits = mpi_reference.quantile(
    upper_quantile,
    interpolation="linear",
)

mpi_analytical = mpi_reference.clip(
    upper=mpi_upper_limits,
    axis="columns",
)

mpi_changed = mpi_analytical.ne(mpi_reference)

# Параметры фиксируются на общей исторической выборке.
mpi_means = mpi_analytical.mean()
mpi_stds = mpi_analytical.std(ddof=0)

if (
    not np.isfinite(mpi_stds.to_numpy()).all()
    or (mpi_stds <= 0).any()
):
    raise ValueError("Invalid MPI standard deviations.")

mpi_normalized = (
    normalized_reference
    + normalized_std_multiplier
    * (mpi_analytical - mpi_means)
    / mpi_stds
)

if (
    not np.isfinite(mpi_normalized.to_numpy()).all()
    or (mpi_normalized <= 0).any().any()
):
    raise ValueError("Invalid MPI normalized values.")


# %%
# Сохраняем аналитические значения отдельно от исходных.
# У неполных/исключенных строк эти столбцы остаются пустыми.

for component in mpi_components:
    analytical_column = f"mpi_analytical_{component}"
    normalized_column = f"mpi_normalized_{component}"
    changed_column = f"mpi_winsorized_{component}"

    bdi_panel[analytical_column] = np.nan
    bdi_panel[normalized_column] = np.nan

    # Nullable boolean: NA означает, что строка не оценивалась.
    bdi_panel[changed_column] = pd.Series(
        pd.NA,
        index=bdi_panel.index,
        dtype="boolean",
    )

    bdi_panel.loc[mpi_mask, analytical_column] = (
        mpi_analytical[component]
    )
    bdi_panel.loc[mpi_mask, normalized_column] = (
        mpi_normalized[component]
    )
    bdi_panel.loc[mpi_mask, changed_column] = (
        mpi_changed[component]
    )


# %%
# Средний уровень, несбалансированность и итоговый MPI.

mpi_mean = mpi_normalized.mean(axis=1)
mpi_variance = mpi_normalized.var(axis=1, ddof=0)
mpi_std = np.sqrt(mpi_variance)
mpi_penalty = mpi_variance / mpi_mean
mpi_score = mpi_mean - mpi_penalty

for column, values in {
    "bdi_mpi_mean": mpi_mean,
    "bdi_mpi_component_std": mpi_std,
    "bdi_mpi_penalty": mpi_penalty,
    "bdi_mpi": mpi_score,
}.items():
    bdi_panel[column] = np.nan
    bdi_panel.loc[mpi_mask, column] = values


# %%
# Локальная монотонность на обработанной выборке.
# За порогом винзоризации исходный компонент имеет насыщение.

mpi_derivatives = pd.DataFrame({
    component: (
        3
        - 2 * mpi_normalized[component] / mpi_mean
        + mpi_variance / mpi_mean ** 2
    ) / len(mpi_components)
    for component in mpi_components
})

mpi_monotonicity = pd.DataFrame({
    "min_local_derivative": mpi_derivatives.min(),
    "nonpositive_derivative_count": (
        mpi_derivatives <= 0
    ).sum(),
})
mpi_monotonicity.index.name = "component"

if (mpi_derivatives <= 0).any().any():
    raise ValueError(
        "MPI local monotonicity violation. "
        "Inspect the specification before saving main outputs."
    )


# %%
# Параметры воспроизводимости нового индекса.

mpi_parameters = pd.DataFrame({
    "upper_quantile": upper_quantile,
    "upper_threshold": mpi_upper_limits,
    "mean_after_winsorization": mpi_means,
    "std_after_winsorization_ddof0": mpi_stds,
    "normalized_reference": normalized_reference,
    "normalized_std_multiplier": normalized_std_multiplier,
    "direction": 1,
    "formal_weight": 1 / len(mpi_components),
    "reference_n": len(mpi_reference),
    "reference_start_year": int(
        bdi_panel.loc[mpi_mask, "year"].min()
    ),
    "reference_end_year": int(
        bdi_panel.loc[mpi_mask, "year"].max()
    ),
    "winsorized_value_count": mpi_changed.sum(),
})
mpi_parameters.index.name = "component"

mpi_changed_observations = bdi_panel.loc[
    mpi_changed.any(axis=1).reindex(
        bdi_panel.index,
        fill_value=False,
    ),
    keys
    + mpi_components
    + [
        f"mpi_analytical_{component}"
        for component in mpi_components
    ],
].copy()

mpi_quality_exclusions = bdi_panel.loc[
    quality_exclusion,
    keys
    + mpi_components
    + ["bdi_mpi_exclusion_reason"],
].copy()

mpi_coverage = (
    bdi_panel.groupby("year")
    .agg(
        total_observations=("bdi_mpi_complete", "size"),
        complete_components=(
            "bdi_mpi_components_complete", "sum"
        ),
        quality_excluded=(
            "bdi_mpi_quality_excluded", "sum"
        ),
        mpi_observations=("bdi_mpi", "count"),
    )
    .reset_index()
)


# %%
# Сохранение

final_dir = project_root / "data/final"
diagnostics_dir = project_root / "outputs/diagnostics"
coverage_dir = project_root / "outputs/coverage"

for directory in [final_dir, diagnostics_dir, coverage_dir]:
    directory.mkdir(parents=True, exist_ok=True)

bdi_panel.to_csv(
    final_dir / "BDI_panel.csv",
    index=False,
)

# Прежние параметры сохраняют прежний смысл.
legacy_parameters.to_csv(
    diagnostics_dir / "normalization_parameters.csv",
    index=True,
)

# Новые параметры имеют отдельное имя.
mpi_parameters.to_csv(
    diagnostics_dir / "bdi_mpi_normalization_parameters.csv",
    index=True,
)

mpi_monotonicity.to_csv(
    diagnostics_dir / "bdi_mpi_monotonicity.csv",
    index=True,
)

mpi_changed_observations.to_csv(
    diagnostics_dir / "bdi_mpi_winsorized_observations.csv",
    index=False,
)

mpi_quality_exclusions.to_csv(
    diagnostics_dir / "bdi_mpi_quality_exclusions.csv",
    index=False,
)

mpi_coverage.to_csv(
    coverage_dir / "bdi_mpi_coverage.csv",
    index=False,
)

print("BDI-panel saved:", bdi_panel.shape)
print("Legacy complete observations:", int(
    bdi_panel["bdi_complete"].sum()
))
print("MPI complete observations:", int(mpi_mask.sum()))
print("MPI quality exclusions:", int(quality_exclusion.sum()))
print("MPI winsorized values:", int(
    mpi_changed.to_numpy().sum()
))
print("MPI affected observations:", int(
    mpi_changed.any(axis=1).sum()
))

print("\nMPI PARAMETERS")
print(mpi_parameters.round(6).to_string())

print("\nMPI MONOTONICITY")
print(mpi_monotonicity.round(6).to_string())

print("\nMPI COVERAGE")
print(mpi_coverage.to_string(index=False))