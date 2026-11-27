# %%
# %%
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import (
    variance_inflation_factor,
)

project_root = Path(__file__).resolve().parents[1]

model_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)


# %%
# Исследовательская корреляция всех кандидатов на полной панели.

candidate_predictors = [
    "investment_intensity",
    "labour_share",
    "average_compensation",
    "value_added_ratio",
    "gfcf_per_employed",
    "labour_productivity",
    "employment_growth",
    "net_operating_surplus_mixed_income_margin",
]

spearman_corr = model_panel[candidate_predictors].corr(
    method="spearman"
)

spearman_corr.to_csv(
    diagnostics_dir / "x_predictor_spearman.csv",
    index=True,
)


# %%
# Модельная выборка нового MPI.

baseline_predictors = [
    "investment_intensity",
    "labour_share",
    "labour_productivity",
    "employment_growth",
]

selected_columns = (
    ["geo", "nace_r2", "year", "bdi_mpi"]
    + baseline_predictors
)

eligible_sample = model_panel.loc[
    model_panel["bdi_mpi_complete"].eq(True),
    selected_columns,
].copy()

baseline_sample = eligible_sample.dropna(
    subset=baseline_predictors + ["bdi_mpi"]
).copy()

if baseline_sample.empty:
    raise ValueError("Empty MPI model sample.")

if baseline_sample.duplicated(
    ["geo", "nace_r2", "year"]
).any():
    raise ValueError("Duplicate model-sample keys.")

numeric_columns = baseline_predictors + ["bdi_mpi"]

if not np.isfinite(
    baseline_sample[numeric_columns].to_numpy()
).all():
    raise ValueError("Non-finite values in the model sample.")

if baseline_sample["labour_productivity"].le(0).any():
    raise ValueError(
        "Labour productivity must be positive before logarithming."
    )

baseline_sample["log_labour_productivity"] = np.log(
    baseline_sample["labour_productivity"]
)


# %%
# Диагностика X на фактической модельной выборке.

model_predictors = [
    "investment_intensity",
    "labour_share",
    "log_labour_productivity",
    "employment_growth",
]

baseline_pearson_corr = baseline_sample[
    model_predictors
].corr(method="pearson")

baseline_pearson_corr.to_csv(
    diagnostics_dir / "baseline_predictor_pearson.csv",
    index=True,
)

vif_design = sm.add_constant(
    baseline_sample[model_predictors],
    has_constant="add",
)

vif_summary = pd.DataFrame({
    "variable": model_predictors,
    "vif": [
        variance_inflation_factor(
            vif_design.to_numpy(),
            vif_design.columns.get_loc(predictor),
        )
        for predictor in model_predictors
    ],
})

vif_summary.to_csv(
    diagnostics_dir / "baseline_vif.csv",
    index=False,
)


# %%
# Сохранение: прежнее имя файла, новая зависимая переменная.

baseline_sample.to_csv(
    project_root / "data/final/baseline_model_sample.csv",
    index=False,
)

print("Eligible MPI observations:", len(eligible_sample))
print(
    "Excluded due to missing model values:",
    len(eligible_sample) - len(baseline_sample),
)
print("MPI model sample saved:", baseline_sample.shape)

print("\nMODEL SAMPLE BY YEAR")
print(baseline_sample.groupby("year").size().to_string())

print("\nPREDICTOR VIF")
print(vif_summary.round(4).to_string(index=False))