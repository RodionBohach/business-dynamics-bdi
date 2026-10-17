# %%
import pandas as pd
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
model_panel = pd.read_csv(project_root / 'data/final/BDI_panel.csv')
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
# %%
candidate_predictors = ['investment_intensity', 'labour_share', 'average_compensation', 'value_added_ratio', 
                        'gfcf_per_employed', 'labour_productivity', 'employment_growth', 'net_operating_surplus_mixed_income_margin']
spearman_corr = model_panel[candidate_predictors].corr(method= 'spearman')
# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)
spearman_corr.to_csv(diagnostics_dir / 'x_predictor_spearman.csv', index = True)
# %%
baseline_predictors = ['investment_intensity', 'labour_share', 'labour_productivity', 'employment_growth']
baseline_sample = model_panel[baseline_predictors + ["geo", "nace_r2", "year", "bdi_zscore"]].dropna().copy()
# %%
baseline_sample['log_labour_productivity'] = np.log(baseline_sample['labour_productivity'])
# %%
model_predictors = ['investment_intensity', 'labour_share', 'log_labour_productivity', 'employment_growth']

# %%
baseline_pearson_corr = baseline_sample[model_predictors].corr(method='pearson')
# %%
baseline_pearson_corr.to_csv(diagnostics_dir / 'baseline_predictor_pearson.csv', index = True)
# %%
vif_design = sm.add_constant(baseline_sample[model_predictors])
# %%
vif_summary = pd.DataFrame({'variable': model_predictors, 'vif': [variance_inflation_factor(vif_design.values, 1),
        variance_inflation_factor(vif_design.values, 2),
        variance_inflation_factor(vif_design.values, 3),
        variance_inflation_factor(vif_design.values, 4),],})
# %%
vif_summary.to_csv(diagnostics_dir / 'baseline_vif.csv', index=False)
# %%
baseline_sample.to_csv(project_root / 'data/final/baseline_model_sample.csv', index=False)