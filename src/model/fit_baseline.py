# %%
import pandas as pd
from pathlib import Path
import statsmodels.api as sm
project_root = Path(__file__).resolve().parents[2]
model_sample = pd.read_csv(project_root / 'data/final/baseline_model_sample.csv')
model_predictors = ['investment_intensity', 'labour_share', 'log_labour_productivity', 'employment_growth']
# %%
y = model_sample['bdi_zscore']
x = sm.add_constant(model_sample[model_predictors])
# %%
baseline_model = sm.OLS(y , x)
baseline_results = baseline_model.fit()
# %%
model_sample['panel_id'] = (model_sample["geo"] + "_" + model_sample["nace_r2"])

# %%
baseline_clustered_results = baseline_model.fit(cov_type="cluster", cov_kwds= {'groups': model_sample["panel_id"]})
# %%
models_dir = project_root / "outputs/models"
models_dir.mkdir(parents=True, exist_ok=True)
# %%
confidence_intervals = baseline_clustered_results.conf_int()
baseline_coefficients = pd.DataFrame({
    "coefficient": baseline_clustered_results.params,
    "std_error": baseline_clustered_results.bse,
    "p_value": baseline_clustered_results.pvalues,
    "ci_lower": confidence_intervals[0],
    "ci_upper": confidence_intervals[1],
})
# %%
baseline_coefficients.to_csv(models_dir / 'pooled_ols_clustered_coefficients.csv', index=True)
# %%
(models_dir / "pooled_ols_clustered_summary.txt").write_text(
    baseline_clustered_results.summary().as_text(),
    encoding="utf-8",
)
# %%
