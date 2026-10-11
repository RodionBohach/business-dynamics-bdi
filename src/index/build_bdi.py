# %%
import pandas as pd
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]

# %%
panel = pd.read_csv(project_root / 'data/final/analytical_panel.csv')
component_directions = {
    'birth_rate': 1,
    'death_rate': -1,
    'survival_3y': 1,
    'high_growth_share': 1
}
# %%
components = list(component_directions)
bdi_panel = panel.copy()
bdi_panel['bdi_complete'] = bdi_panel[components].notna().all(axis=1)
# %%
normalization_sample = bdi_panel.loc[bdi_panel["bdi_complete"], components].copy()
# %%
component_means = normalization_sample.mean()
component_stds = normalization_sample.std(ddof=0)
# %%
z_scores = (bdi_panel[components] - component_means) / component_stds
directions = pd.Series(component_directions)
z_scores_directed = z_scores * directions
# %%
bdi_panel['bdi_zscore'] = z_scores_directed.mean(axis=1, skipna=False)
# %%
component_mins = normalization_sample.min()
component_maxs = normalization_sample.max()
component_ranges = component_maxs - component_mins
# %%
minmax_scores = (bdi_panel[components] - component_mins) / component_ranges
minmax_scores_directed = minmax_scores.copy()
minmax_scores_directed['death_rate'] = 1 - minmax_scores['death_rate']
# %%
bdi_panel['bdi_minmax'] = minmax_scores_directed.mean(axis= 1, skipna=False)
# %%
normalization_parameters = pd.DataFrame({'mean': component_means,
'std': component_stds,
'min': component_mins,
'max': component_maxs,
'direction': directions}).rename_axis("component").reset_index()
# %%
normalization_parameters = normalization_parameters.assign(weight = 1 / len(components), reference_n = len(normalization_sample))
# %%
final_dir = project_root / 'data/final'
final_dir.mkdir(parents=True, exist_ok=True)
diagnostics_dir = project_root / 'outputs/diagnostics'
diagnostics_dir.mkdir(parents=True, exist_ok=True)
assert bdi_panel.shape == (1920, 27), "Unexpected panel shape"
assert bdi_panel['bdi_zscore'].isna().sum() == 2, "Unexpected z-score BDI missing count"
assert bdi_panel['bdi_minmax'].isna().sum() == 2, "Unexpected min-max BDI missing count"
assert bdi_panel.duplicated(subset=['geo', 'nace_r2', 'year'], keep=False).sum() == 0, "Duplicate BDI-panel keys"
bdi_panel.to_csv(final_dir / 'BDI_panel.csv', index=False)
normalization_parameters.to_csv(diagnostics_dir / 'normalization_parameters.csv', index=False)
print("BDI-panel saved:", bdi_panel.shape)
# %%

# %%
