# %%
import pandas as pd
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

project_root = Path(__file__).resolve().parents[2]
fit_model = pd.read_csv(project_root / 'data/final/baseline_model_sample.csv')
fit_effects = ['investment_intensity', 'labour_share', 'log_labour_productivity', 'employment_growth']
fit_model['panel_id'] = (fit_model['geo'] + '_' + fit_model['nace_r2'])
# %%
fe_formula = (
    "bdi_zscore ~ investment_intensity + labour_share "
    "+ log_labour_productivity + employment_growth "
    "+ C(panel_id) + C(year)"
)
# %%
fe_model = smf.ols(fe_formula, data=fit_model)
fe_results = fe_model.fit(cov_type="cluster", cov_kwds = {'groups': fit_model['panel_id']})
# %%
within_predictors = fit_model[fit_effects].copy()
investment_fe_projection = smf.ols("investment_intensity ~ C(panel_id) + C(year)", data=fit_model).fit()
labour_fe_projection = smf.ols("labour_share ~ C(panel_id) + C(year)", data=fit_model).fit()
log_labour_fe_projection = smf.ols("log_labour_productivity ~ C(panel_id) + C(year)", data=fit_model).fit()
employment_fe_projection = smf.ols("employment_growth ~ C(panel_id) + C(year)", data=fit_model).fit()

# %%
within_predictors['investment_intensity'] = investment_fe_projection.resid
within_predictors['labour_share'] = labour_fe_projection.resid
within_predictors['log_labour_productivity'] = log_labour_fe_projection.resid
within_predictors['employment_growth'] = employment_fe_projection.resid
# %%
within_pearson_corr = within_predictors.corr(method="pearson")
# %%
within_vif_design = sm.add_constant(within_predictors)
within_vif_summary = pd.DataFrame({
    "variable": fit_effects,
    "vif": [
        variance_inflation_factor(within_vif_design.values, 1),
        variance_inflation_factor(within_vif_design.values, 2),
        variance_inflation_factor(within_vif_design.values, 3),
        variance_inflation_factor(within_vif_design.values, 4),
    ],
})

# %%
fit_dir = project_root / "outputs/models"
fit_dir.mkdir(parents=True, exist_ok=True)
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

within_pearson_corr.to_csv(
    diagnostics_dir / "fe_within_predictor_pearson.csv",
    index=True,
)
within_vif_summary.to_csv(
    diagnostics_dir / "fe_within_vif.csv",
    index=False,
)
# %%
fe_confidence_intervals = fe_results.conf_int()
fe_coefficients = pd.DataFrame({
    'coefficient' : fe_results.params,
    'std_error': fe_results.bse,
    'p_value': fe_results.pvalues,
    'ci_lower': fe_confidence_intervals[0],
    'ci_upper': fe_confidence_intervals[1],

},
)
fe_coefficients = fe_coefficients.loc[fit_effects].copy()
# %%
fe_coefficients.to_csv(fit_dir / 'fixed_effects_clustered_coefficients.csv', index=True)
# %%
(fit_dir / "fixed_effects_clustered_summary.txt").write_text(
    fe_results.summary().as_text(),
    encoding="utf-8",
)
# %%
fe_observation_diagnostics = fit_model[['geo', 'nace_r2', 'year', 'bdi_zscore']].copy()
fe_observation_diagnostics['fitted'] = fe_results.fittedvalues
fe_observation_diagnostics['residual'] = fe_results.resid
fe_observation_diagnostics['abs_residual'] = fe_observation_diagnostics["residual"].abs()

# %%
figures_dir = project_root / "outputs/figures"
figures_dir.mkdir(parents=True, exist_ok=True)
plt.figure(figsize=(8, 5))
plt.scatter(
    fe_observation_diagnostics["fitted"],
    fe_observation_diagnostics["residual"],
    alpha=0.5,
    s=15,
)
plt.axhline(y=0, color="gray", linestyle="--")
plt.xlabel("Fitted BDI")
plt.ylabel("Residual")
plt.title("FE model: residuals versus fitted values")
plt.tight_layout()
plt.savefig(figures_dir/ "fe_residuals_vs_fitted.png", dpi=300, bbox_inches="tight")
plt.show()
# %%

fe_observation_diagnostics.to_csv(diagnostics_dir / 'fe_observation_diagnostics.csv', index=False)
# %%
fe_influence = fe_results.get_influence()
# %%
fe_observation_diagnostics['leverage'] = fe_influence.hat_matrix_diag
fe_observation_diagnostics['cooks_distance'] = fe_influence.cooks_distance[0]
# %%
fe_observation_diagnostics.to_csv(diagnostics_dir / 'fe_observation_diagnostics.csv')
fe_sensitivity_exclusion_mask = (((fit_model['geo'] == 'PT') & (fit_model['nace_r2'] == 'D') & (fit_model['year'] == 2016))
|
((fit_model['geo'] == 'NO') & (fit_model['nace_r2'] == 'D') & (fit_model['year'] == 2020))
|
((fit_model['geo'] == 'RO') & (fit_model['nace_r2'] == 'M') & (fit_model['year'] == 2013)))



# %%
fe_sensitivity_sample = fit_model[~fe_sensitivity_exclusion_mask].copy()
# %%
fe_sensitivity_results = smf.ols(fe_formula, data=fe_sensitivity_sample,).fit(cov_type="cluster",cov_kwds={"groups": fe_sensitivity_sample["panel_id"]},)
# %%
fe_sensitivity_comparison = pd.DataFrame({
    "baseline_coefficient": fe_results.params.loc[fit_effects],
    "sensitivity_coefficient": fe_sensitivity_results.params.loc[fit_effects],
    "baseline_p_value": fe_results.pvalues.loc[fit_effects],
    "sensitivity_p_value": fe_sensitivity_results.pvalues.loc[fit_effects],
})
# %%
fe_sensitivity_comparison.to_csv(fit_dir / 'fixed_effects_sensitivity_comparison.csv', index=True)
# %%
fe_country_clustered_results = fe_model.fit(cov_type="cluster", cov_kwds={'groups': fit_model['geo']}, use_t=True)
country_confidence_intervals = fe_country_clustered_results.conf_int()

fe_country_clustered_coefficients = pd.DataFrame({
    "coefficient": fe_country_clustered_results.params.loc[fit_effects],
    "std_error": fe_country_clustered_results.bse.loc[fit_effects],
    "p_value": fe_country_clustered_results.pvalues.loc[fit_effects],
    "ci_lower": country_confidence_intervals.loc[fit_effects, 0],
    "ci_upper": country_confidence_intervals.loc[fit_effects, 1],
})
# %%
fe_country_clustered_coefficients.to_csv(fit_dir / 'fixed_effects_country_clustered_coefficients.csv', index=True)
fe_pair_clustered_t_results = fe_model.fit(cov_type="cluster", cov_kwds={'groups': fit_model['panel_id']}, use_t=True)
# %%
fe_clustering_comparison = pd.DataFrame({
    'coefficient' : fe_pair_clustered_t_results.params.loc[fit_effects],
    'pair_std_error' : fe_pair_clustered_t_results.bse.loc[fit_effects],
    'country_std_error': fe_country_clustered_results.bse.loc[fit_effects],
    'pair_p_value' : fe_pair_clustered_t_results.pvalues.loc[fit_effects],
    'country_p_value' :fe_country_clustered_results.pvalues.loc[fit_effects]
})
# %%
fe_clustering_comparison.to_csv(fit_dir / 'fixed_effects_clustering_comparison.csv', index=True)
# %%
bdi_source = pd.read_csv(project_root / "data/final/BDI_panel.csv")
# %%
bdi_alternative_columns = bdi_source[['geo', 'nace_r2', 'year', 'bdi_minmax']]
# %%
fe_alternative_sample = fit_model.merge(bdi_alternative_columns, on=['geo', 'nace_r2', 'year'], how='left', validate="one_to_one")
# %%
fe_minmax_formula = (
    "bdi_minmax ~ investment_intensity + labour_share "
    "+ log_labour_productivity + employment_growth "
    "+ C(panel_id) + C(year)"
)
# %%
fe_minmax_model = smf.ols(fe_minmax_formula, data=fe_alternative_sample)
fe_minmax_results = fe_minmax_model.fit(cov_type="cluster", cov_kwds = {'groups': fe_alternative_sample["geo"]}, use_t=True)
# %%
fe_minmax_intervals = fe_minmax_results.conf_int()

fe_minmax_coefficients = pd.DataFrame({
    "coefficient": fe_minmax_results.params.loc[fit_effects],
    "std_error": fe_minmax_results.bse.loc[fit_effects],
    "p_value": fe_minmax_results.pvalues.loc[fit_effects],
    "ci_lower": fe_minmax_intervals.loc[fit_effects, 0],
    "ci_upper": fe_minmax_intervals.loc[fit_effects, 1],
})
# %%
fe_minmax_coefficients.to_csv(fit_dir / 'fixed_effects_minmax_country_clustered_coefficients.csv', index=True)
# %%
