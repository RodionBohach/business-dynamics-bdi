# %%
import pandas as pd
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]


# %%
y_panel = pd.read_csv(project_root / "data/final/Y_panel.csv")
x_panel = pd.read_csv(project_root / "data/final/X_panel.csv")
# %%
panel_keys = ['geo', 'nace_r2', 'year']
# %%
analytical_panel = y_panel.merge(x_panel, how='outer', on=panel_keys, validate='one_to_one', indicator=True)
# %%
assert (analytical_panel["_merge"] == "both").all(), "Unmatched X/Y keys"
# %%
analytical_panel = analytical_panel.drop(columns=['_merge'])
# %%
assert analytical_panel.shape == (1920, 24), "Unexpected panel shape"
assert analytical_panel["survival_3y"].isna().sum() == 2, "Unexpected survival missing count"
assert analytical_panel.isna().sum().sum() == 2, "Unexpected total missing count"
final_dir = project_root / "data/final"
final_dir.mkdir(parents=True, exist_ok=True)
analytical_panel.to_csv(final_dir / "analytical_panel.csv", index=False)
# %%
print("Analytical panel saved:", analytical_panel.shape)
# %%
analytical_panel_check = pd.read_csv(final_dir / "analytical_panel.csv")
# %%
