# %%
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import (
    variance_inflation_factor,
)

project_root = Path(__file__).resolve().parents[2]

fit_model = pd.read_csv(
    project_root / "data/final/baseline_model_sample.csv"
)

fit_effects = [
    "investment_intensity",
    "labour_share",
    "log_labour_productivity",
    "employment_growth",
]

keys = ["geo", "nace_r2", "year"]

fit_model["panel_id"] = (
    fit_model["geo"] + "_" + fit_model["nace_r2"]
)

if fit_model.duplicated(keys).any():
    raise ValueError("Duplicate model keys.")

if not np.isfinite(
    fit_model[fit_effects + ["bdi_mpi"]].to_numpy()
).all():
    raise ValueError("Missing or non-finite model values.")

models_dir = project_root / "outputs/models"
diagnostics_dir = project_root / "outputs/diagnostics"

models_dir.mkdir(parents=True, exist_ok=True)
diagnostics_dir.mkdir(parents=True, exist_ok=True)


# %%
# Вспомогательные функции

rhs = (
    "investment_intensity + labour_share "
    "+ log_labour_productivity + employment_growth "
    "+ C(panel_id) + C(year)"
)


def fit_clustered(data, outcome, cluster_column):
    return smf.ols(
        f"{outcome} ~ {rhs}",
        data=data,
        missing="raise",
    ).fit(
        cov_type="cluster",
        cov_kwds={"groups": data[cluster_column]},
        use_t=True,
    )


def coefficient_table(results):
    intervals = results.conf_int()

    table = pd.DataFrame({
        "coefficient": results.params.loc[fit_effects],
        "std_error": results.bse.loc[fit_effects],
        "p_value": results.pvalues.loc[fit_effects],
        "ci_lower": intervals.loc[fit_effects, 0],
        "ci_upper": intervals.loc[fit_effects, 1],
    })
    table.index.name = "variable"
    return table


# %%
# Одинаковая FE-спецификация, два уровня кластеризации.
# use_t=True применяется в обоих вариантах.

fe_pair_results = fit_clustered(
    fit_model, "bdi_mpi", "panel_id"
)

fe_country_results = fit_clustered(
    fit_model, "bdi_mpi", "geo"
)

pair_coefficients = coefficient_table(fe_pair_results)
country_coefficients = coefficient_table(fe_country_results)

pair_coefficients.to_csv(
    models_dir / "fixed_effects_mpi_pair_clustered_coefficients.csv"
)
country_coefficients.to_csv(
    models_dir / "fixed_effects_mpi_country_clustered_coefficients.csv"
)

clustering_comparison = pd.DataFrame({
    "coefficient": fe_pair_results.params.loc[fit_effects],
    "pair_std_error": fe_pair_results.bse.loc[fit_effects],
    "country_std_error": fe_country_results.bse.loc[fit_effects],
    "pair_p_value": fe_pair_results.pvalues.loc[fit_effects],
    "country_p_value": fe_country_results.pvalues.loc[fit_effects],
})
clustering_comparison.index.name = "variable"

clustering_comparison.to_csv(
    models_dir / "fixed_effects_mpi_clustering_comparison.csv"
)

# summary() может выдавать знакомое предупреждение
# о ранге ограничений. Общий F-тест всех FE не интерпретируем.
for label, results in {
    "pair": fe_pair_results,
    "country": fe_country_results,
}.items():
    (
        models_dir
        / f"fixed_effects_mpi_{label}_clustered_summary.txt"
    ).write_text(
        "\n".join(
    line.rstrip()
    for line in results.summary().as_text().splitlines()
) + "\n",
        encoding="utf-8",
    )


# %%
# Корреляции и VIF после удаления фиксированных эффектов

within_predictors = pd.DataFrame(index=fit_model.index)

for predictor in fit_effects:
    projection = smf.ols(
        f"{predictor} ~ C(panel_id) + C(year)",
        data=fit_model,
        missing="raise",
    ).fit()

    within_predictors[predictor] = projection.resid

within_predictors.corr(method="pearson").to_csv(
    diagnostics_dir / "fe_mpi_within_predictor_pearson.csv"
)

within_design = sm.add_constant(
    within_predictors,
    has_constant="add",
)

within_vif = pd.DataFrame({
    "variable": fit_effects,
    "vif": [
        variance_inflation_factor(
            within_design.to_numpy(),
            within_design.columns.get_loc(predictor),
        )
        for predictor in fit_effects
    ],
})

within_vif.to_csv(
    diagnostics_dir / "fe_mpi_within_vif.csv",
    index=False,
)

within_stds = within_predictors.std(ddof=0)
within_stds.to_csv(
    diagnostics_dir / "fe_mpi_within_predictor_stds.csv",
    header=["within_std"],
)


# %%
# Остатки и обычные OLS-диагностики влияния.
# Cook's distance не является кластерно-робастной диагностикой.

observation_diagnostics = fit_model[
    keys + ["bdi_mpi"]
].copy()

observation_diagnostics["fitted"] = (
    fe_country_results.fittedvalues
)
observation_diagnostics["residual"] = (
    fe_country_results.resid
)
observation_diagnostics["abs_residual"] = (
    observation_diagnostics["residual"].abs()
)

influence = fe_country_results.get_influence()

observation_diagnostics["leverage"] = (
    influence.hat_matrix_diag
)
observation_diagnostics["cooks_distance"] = (
    influence.cooks_distance[0]
)

observation_diagnostics.to_csv(
    diagnostics_dir / "fe_mpi_observation_diagnostics.csv",
    index=False,
)


# %%
# Средний уровень без штрафа.
# Те же обработанные компоненты, нормализация и модельная выборка.

bdi_source = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

mean_sample = fit_model.merge(
    bdi_source[keys + ["bdi_mpi_mean"]],
    on=keys,
    how="left",
    validate="one_to_one",
)

if not np.isfinite(mean_sample["bdi_mpi_mean"]).all():
    raise ValueError("Missing mean-score alternative.")

mean_results = fit_clustered(
    mean_sample, "bdi_mpi_mean", "geo"
)

mean_coefficients = coefficient_table(mean_results)

mean_coefficients.to_csv(
    models_dir
    / "fixed_effects_mpi_mean_country_clustered_coefficients.csv"
)

penalty_comparison = pd.DataFrame({
    "mpi_coefficient": fe_country_results.params.loc[fit_effects],
    "mean_coefficient": mean_results.params.loc[fit_effects],
    "mpi_std_error": fe_country_results.bse.loc[fit_effects],
    "mean_std_error": mean_results.bse.loc[fit_effects],
    "mpi_p_value": fe_country_results.pvalues.loc[fit_effects],
    "mean_p_value": mean_results.pvalues.loc[fit_effects],
})
penalty_comparison.index.name = "variable"

penalty_comparison.to_csv(
    models_dir / "fixed_effects_mpi_penalty_comparison.csv"
)


# %%
# Чувствительность модели к составу наблюдений.
# Значения MPI, пороги и нормализация остаются фиксированными.
# Это проверка оценки регрессии, а не пересчет самого индекса.

pt_d_2016 = (
    (fit_model["geo"] == "PT")
    & (fit_model["nace_r2"] == "D")
    & (fit_model["year"] == 2016)
)

no_d = (
    (fit_model["geo"] == "NO")
    & (fit_model["nace_r2"] == "D")
)

sensitivity_parts = []
model_information = []


def information_row(label, data, results):
    return {
        "specification": label,
        "outcome": results.model.endog_names,
        "n_observations": int(results.nobs),
        "n_pairs": data["panel_id"].nunique(),
        "n_countries": data["geo"].nunique(),
        "r_squared_including_fe": results.rsquared,
        "adjusted_r_squared": results.rsquared_adj,
    }


model_information.append(
    information_row(
        "mpi_country_clustered", fit_model, fe_country_results
    )
)
model_information.append(
    information_row(
        "mean_country_clustered", mean_sample, mean_results
    )
)

for scenario, exclusion_mask in {
    "exclude_pt_d_2016": pt_d_2016,
    "exclude_all_no_d": no_d,
}.items():
    sensitivity_sample = fit_model.loc[
        ~exclusion_mask
    ].copy()

    sensitivity_results = fit_clustered(
        sensitivity_sample, "bdi_mpi", "geo"
    )

    comparison = pd.DataFrame({
        "baseline_coefficient": (
            fe_country_results.params.loc[fit_effects]
        ),
        "sensitivity_coefficient": (
            sensitivity_results.params.loc[fit_effects]
        ),
        "baseline_std_error": (
            fe_country_results.bse.loc[fit_effects]
        ),
        "sensitivity_std_error": (
            sensitivity_results.bse.loc[fit_effects]
        ),
        "baseline_p_value": (
            fe_country_results.pvalues.loc[fit_effects]
        ),
        "sensitivity_p_value": (
            sensitivity_results.pvalues.loc[fit_effects]
        ),
    })
    comparison.index.name = "variable"
    comparison = comparison.reset_index()
    comparison.insert(0, "scenario", scenario)
    sensitivity_parts.append(comparison)

    model_information.append(
        information_row(
            scenario,
            sensitivity_sample,
            sensitivity_results,
        )
    )

sensitivity_comparison = pd.concat(
    sensitivity_parts,
    ignore_index=True,
)

sensitivity_comparison.to_csv(
    models_dir / "fixed_effects_mpi_sample_sensitivity.csv",
    index=False,
)

model_information = pd.DataFrame(model_information)

model_information.to_csv(
    models_dir / "fixed_effects_mpi_model_information.csv",
    index=False,
)


# %%
# Масштабирование коэффициентов на одно within-отклонение X.
# Интервалы используют кластеризацию по стране.

scaled_coefficients = country_coefficients.join(
    within_stds.rename("within_std")
)

for source, target in {
    "coefficient": "scaled_coefficient",
    "ci_lower": "scaled_ci_lower",
    "ci_upper": "scaled_ci_upper",
}.items():
    scaled_coefficients[target] = (
        scaled_coefficients[source]
        * scaled_coefficients["within_std"]
    )

scaled_coefficients.to_csv(
    models_dir / "fixed_effects_mpi_scaled_coefficients.csv"
)


# %%
print("\nMPI FE MODEL INFORMATION")
print(model_information.round(4).to_string(index=False))

print("\nMPI FE CLUSTERING COMPARISON")
print(clustering_comparison.round(6).to_string())

print("\nMPI FE COUNTRY-CLUSTERED COEFFICIENTS")
print(country_coefficients.round(6).to_string())

print("\nMPI FE WITHIN VIF")
print(within_vif.round(4).to_string(index=False))

print("\nMPI FE PENALTY COMPARISON")
print(penalty_comparison.round(6).to_string())

print("\nMPI FE SAMPLE SENSITIVITY")
print(
    sensitivity_comparison.round(6).to_string(index=False)
)

# %%
# Диагностика новой FE-модели MPI

diagnostic_columns = [
    "geo",
    "nace_r2",
    "year",
    "bdi_mpi",
    "fitted",
    "residual",
    "leverage",
    "cooks_distance",
]

largest_residuals = observation_diagnostics.nlargest(
    10, "abs_residual"
)[diagnostic_columns].copy()

largest_cooks_distance = observation_diagnostics.nlargest(
    10, "cooks_distance"
)[diagnostic_columns].copy()

largest_leverage = observation_diagnostics.nlargest(
    10, "leverage"
)[diagnostic_columns].copy()

diagnostic_summary = observation_diagnostics[
    ["residual", "abs_residual", "leverage", "cooks_distance"]
].describe(percentiles=[0.5, 0.9, 0.95, 0.99])

largest_residuals.to_csv(
    diagnostics_dir / "fe_mpi_largest_residuals.csv",
    index=False,
)

largest_cooks_distance.to_csv(
    diagnostics_dir / "fe_mpi_largest_cooks_distance.csv",
    index=False,
)

largest_leverage.to_csv(
    diagnostics_dir / "fe_mpi_largest_leverage.csv",
    index=False,
)

diagnostic_summary.to_csv(
    diagnostics_dir / "fe_mpi_diagnostic_summary.csv",
    index=True,
)

print("\nMPI FE DIAGNOSTIC SUMMARY")
print(diagnostic_summary.round(5).to_string())

print("\nMPI FE LARGEST RESIDUALS")
print(largest_residuals.round(5).to_string(index=False))

print("\nMPI FE LARGEST COOK'S DISTANCE")
print(largest_cooks_distance.round(5).to_string(index=False))

print("\nMPI FE LARGEST LEVERAGE")
print(largest_leverage.round(5).to_string(index=False))
# %%
# %%
# Профили трех наблюдений с наибольшим Cook's distance

selected_cases = observation_diagnostics.nlargest(
    3, "cooks_distance"
)[keys]

profile_columns = (
    keys
    + ["birth_rate", "survival_3y", "high_growth_share"]
    + [
        "mpi_analytical_birth_rate",
        "mpi_analytical_survival_3y",
        "mpi_analytical_high_growth_share",
        "bdi_mpi_mean",
        "bdi_mpi_penalty",
        "bdi_mpi",
    ]
)

influential_profiles = selected_cases.merge(
    bdi_source[profile_columns],
    on=keys,
    how="left",
    validate="one_to_one",
).merge(
    observation_diagnostics[
        keys + ["fitted", "residual", "cooks_distance"]
    ],
    on=keys,
    how="left",
    validate="one_to_one",
)

influential_profiles.to_csv(
    diagnostics_dir / "fe_mpi_influential_profiles.csv",
    index=False,
)

print("\nMPI FE INFLUENTIAL PROFILES")
print(
    influential_profiles.round(4).to_string(index=False)
)

# %%
# Диагностическая чувствительность к трем лидерам Cook's distance.
# Строки не удаляются из основной выборки.
# Значения MPI и параметры его расчета остаются фиксированными.

top_three_keys = pd.MultiIndex.from_frame(selected_cases[keys])
model_keys = pd.MultiIndex.from_frame(fit_model[keys])

influence_sensitivity_sample = fit_model.loc[
    ~model_keys.isin(top_three_keys)
].copy()

influence_sensitivity_results = fit_clustered(
    influence_sensitivity_sample,
    "bdi_mpi",
    "geo",
)

influence_sensitivity_comparison = pd.DataFrame({
    "baseline_coefficient": (
        fe_country_results.params.loc[fit_effects]
    ),
    "sensitivity_coefficient": (
        influence_sensitivity_results.params.loc[fit_effects]
    ),
    "baseline_std_error": (
        fe_country_results.bse.loc[fit_effects]
    ),
    "sensitivity_std_error": (
        influence_sensitivity_results.bse.loc[fit_effects]
    ),
    "baseline_p_value": (
        fe_country_results.pvalues.loc[fit_effects]
    ),
    "sensitivity_p_value": (
        influence_sensitivity_results.pvalues.loc[fit_effects]
    ),
})
influence_sensitivity_comparison.index.name = "variable"

influence_sensitivity_comparison.to_csv(
    models_dir / "fixed_effects_mpi_influence_sensitivity.csv",
    index=True,
)

print("\nMPI FE INFLUENCE SENSITIVITY SAMPLE")
print("Observations:", len(influence_sensitivity_sample))
print(
    "Pairs:",
    influence_sensitivity_sample["panel_id"].nunique(),
)

print("\nMPI FE INFLUENCE SENSITIVITY")
print(
    influence_sensitivity_comparison.round(6).to_string()
)