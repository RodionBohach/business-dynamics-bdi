# %%
from pathlib import Path

import pandas as pd


project_root = Path(__file__).resolve().parents[1]
models_dir = project_root / "outputs/models"

predictors = [
    "investment_intensity",
    "labour_share",
    "log_labour_productivity",
    "employment_growth",
]

specifications = {
    "pooled_mpi_pair": {
        "filename": "pooled_ols_mpi_pair_clustered_coefficients.csv",
        "outcome": "bdi_mpi",
        "fixed_effects": "none",
        "clustering": "country_industry",
        "inference": "normal",
    },
    "fe_mpi_pair": {
        "filename": "fixed_effects_mpi_pair_clustered_coefficients.csv",
        "outcome": "bdi_mpi",
        "fixed_effects": "country_industry_and_year",
        "clustering": "country_industry",
        "inference": "t",
    },
    "fe_mpi_country": {
        "filename": "fixed_effects_mpi_country_clustered_coefficients.csv",
        "outcome": "bdi_mpi",
        "fixed_effects": "country_industry_and_year",
        "clustering": "country",
        "inference": "t",
    },
    "fe_mean_country": {
        "filename": "fixed_effects_mpi_mean_country_clustered_coefficients.csv",
        "outcome": "bdi_mpi_mean",
        "fixed_effects": "country_industry_and_year",
        "clustering": "country",
        "inference": "t",
    },
}

comparison_parts = []

for label, specification in specifications.items():
    coefficients = pd.read_csv(
        models_dir / specification["filename"],
        index_col=0,
    )

    if coefficients.index.duplicated().any():
        raise ValueError(f"Duplicate coefficient names: {label}")

    missing_predictors = set(predictors) - set(coefficients.index)

    if missing_predictors:
        raise ValueError(
            f"Missing predictors in {label}: {missing_predictors}"
        )

    selected = coefficients.loc[predictors].copy()

    selected.index.name = "variable"
    selected = selected.reset_index()

    selected.insert(0, "specification", label)

    for field in [
        "outcome",
        "fixed_effects",
        "clustering",
        "inference",
    ]:
        selected[field] = specification[field]

    comparison_parts.append(selected)

model_comparison = pd.concat(
    comparison_parts,
    ignore_index=True,
)

model_comparison.to_csv(
    models_dir / "mpi_model_comparison.csv",
    index=False,
)


# %%
# Компактные таблицы для последующей аналитики

coefficient_comparison = model_comparison.pivot(
    index="variable",
    columns="specification",
    values="coefficient",
).reindex(predictors)

p_value_comparison = model_comparison.pivot(
    index="variable",
    columns="specification",
    values="p_value",
).reindex(predictors)

coefficient_comparison.to_csv(
    models_dir / "mpi_model_coefficient_comparison.csv"
)

p_value_comparison.to_csv(
    models_dir / "mpi_model_p_value_comparison.csv"
)


# %%
# Читаем уже рассчитанные масштабированные коэффициенты.
# Источник — FE-модель с кластеризацией по стране.

scaled_coefficients = pd.read_csv(
    models_dir / "fixed_effects_mpi_scaled_coefficients.csv",
    index_col=0,
).loc[predictors]

print("\nMPI MODEL COEFFICIENT COMPARISON")
print(coefficient_comparison.round(6).to_string())

print("\nMPI MODEL P-VALUE COMPARISON")
print(p_value_comparison.round(6).to_string())

print("\nMPI COUNTRY-CLUSTERED SCALED COEFFICIENTS")
print(
    scaled_coefficients[
        [
            "within_std",
            "scaled_coefficient",
            "scaled_ci_lower",
            "scaled_ci_upper",
        ]
    ].round(6).to_string()
)

print(
    "\nPooled pair-clustered inference uses the normal distribution; "
    "FE comparisons use t-based inference."
)