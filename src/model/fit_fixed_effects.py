# %%
import pandas as pd
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.formula.api as smf
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
