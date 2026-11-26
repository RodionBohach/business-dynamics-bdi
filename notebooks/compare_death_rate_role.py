# %%
from pathlib import Path

import pandas as pd
project_root = Path(__file__).resolve().parents[1]

# %%
bdi_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

normalization_parameters = pd.read_csv(
    project_root / "outputs/diagnostics/normalization_parameters.csv",
    index_col="component",
)

# %%
bdi_panel_mask = bdi_panel["bdi_complete"] == True
comparison_sample = bdi_panel[bdi_panel_mask].copy()
# %%
retained_components = ['birth_rate', 'survival_3y', 'high_growth_share']
# %%
retained_means = normalization_parameters.loc[retained_components, "mean"]
retained_stds = normalization_parameters.loc[retained_components, "std"]
# %%
retained_z_scores = (
    (comparison_sample[retained_components] - retained_means) / retained_stds
)

comparison_sample['bdi_without_death'] = retained_z_scores.mean(axis=1, skipna=False)
# %%
death_role_spearman = comparison_sample[['bdi_zscore', 'bdi_without_death']].corr(method='spearman').iloc[0, 1]
# %%
rank_original = comparison_sample['bdi_zscore'].rank(ascending=False, method="average")
rank_without_death = comparison_sample['bdi_without_death'].rank(ascending=False, method="average")
# %%
comparison_sample["rank_shift_abs"] = (rank_original - rank_without_death).abs()
# %%
largest_rank_shifts = comparison_sample.nlargest(
    10, "rank_shift_abs",
)[['geo', 'nace_r2', 'year', 'birth_rate', 'death_rate', 'survival_3y', 'high_growth_share', 'bdi_zscore', 'bdi_without_death', 'rank_shift_abs']].copy()
# %%
comparison_sample['churn'] = comparison_sample['birth_rate'] + comparison_sample['death_rate']
comparison_sample['rank_original'] = rank_original
comparison_sample['rank_without_death'] = rank_without_death
comparison_sample['rank_improvement_without_death'] = comparison_sample['rank_original'] - comparison_sample['rank_without_death']
# %%
largest_rank_shifts_2 = comparison_sample.nlargest(
    10, "rank_shift_abs",
)[['geo', 'nace_r2', 'year', 'birth_rate', 'death_rate', 'survival_3y', 'high_growth_share', 'bdi_zscore', 'bdi_without_death', 'rank_shift_abs', 'churn', 'rank_original', 'rank_without_death', 'rank_improvement_without_death']].copy()

# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

comparison_sample.to_csv(
    diagnostics_dir / "bdi_death_role_comparison.csv",
    index=False,
)

largest_rank_shifts_2.to_csv(
    diagnostics_dir / "bdi_death_role_largest_rank_shifts.csv",
    index=False,
)

comparison_sample["rank_shift_abs"].describe(
    percentiles=[0.5, 0.9, 0.95]
).to_csv(
    diagnostics_dir / "bdi_death_role_rank_shift_summary.csv",
    header=["rank_shift_abs"],
)
# %%
pd.DataFrame({
    "comparison": ["original_bdi_vs_bdi_without_death"],
    "spearman_rho": [death_role_spearman],
    "n_observations": [len(comparison_sample)],
}).to_csv(
    diagnostics_dir / "bdi_death_role_spearman.csv",
    index=False,
)
# %%
