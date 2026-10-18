# %%
import pandas as pd
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
models_dir = project_root / 'outputs/models'
fe_zscore = pd.read_csv(models_dir / 'fixed_effects_country_clustered_coefficients.csv', index_col=0)
fe_minmax = pd.read_csv(models_dir / 'fixed_effects_minmax_country_clustered_coefficients.csv', index_col=0)
import matplotlib.pyplot as plt
# %%
fe_zscore["normalization"] = "zscore"
fe_minmax["normalization"] = "minmax"
fe_normalization_comparison = pd.concat([fe_zscore, fe_minmax])
# %%
fe_normalization_comparison = (fe_normalization_comparison.rename_axis("variable").reset_index())
fe_normalization_comparison.to_csv(models_dir / "fixed_effects_normalization_comparison.csv",index=False,)

# %%
within_stds = pd.read_csv(project_root /'outputs/diagnostics/fe_within_predictor_stds.csv', index_col=0)
# %%
fe_coefficient_plot_data = within_stds.join(fe_zscore)
# %%
fe_coefficient_plot_data["scaled_coefficient"] = (
    fe_coefficient_plot_data["coefficient"]
    * fe_coefficient_plot_data["within_std"]
)
fe_coefficient_plot_data["scaled_ci_lower"] = (
    fe_coefficient_plot_data["ci_lower"]
    * fe_coefficient_plot_data["within_std"]
)
fe_coefficient_plot_data["scaled_ci_upper"] = (
    fe_coefficient_plot_data["ci_upper"]
    * fe_coefficient_plot_data["within_std"]
)
# %%
fe_coefficient_plot_data.to_csv(models_dir / 'fixed_effects_scaled_coefficients.csv', index=True)
# %%
lower_errors = (fe_coefficient_plot_data["scaled_coefficient"]- fe_coefficient_plot_data["scaled_ci_lower"])
upper_errors = (fe_coefficient_plot_data["scaled_ci_upper"]- fe_coefficient_plot_data["scaled_coefficient"])
# %%
figures_dir = project_root / "outputs/figures"
figures_dir.mkdir(parents=True, exist_ok=True)
plt.figure(figsize=(9, 5))
plt.gca().invert_yaxis()
plt.xlabel("Change in BDI per within-standard-deviation increase in X")
plt.title('Fixed-effects coefficients with 95% country-clustered confidence intervals')
plt.axvline(x=0, color="gray", linestyle="--")
plt.errorbar(x=fe_coefficient_plot_data['scaled_coefficient'], y=fe_coefficient_plot_data.index, xerr=[lower_errors, upper_errors], fmt="o", capsize=4)
plt.tight_layout()

plt.savefig(figures_dir/ "fe_scaled_coefficients.png", dpi=300, bbox_inches="tight")
plt.show()
# %%
