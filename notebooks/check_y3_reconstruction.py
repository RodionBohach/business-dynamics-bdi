# %%
import pandas as pd
from pathlib import Path
import sys
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from data.load_eurostat import load_eurostat_data

# %%
modern_demography = load_eurostat_data(
    project_root / "data/raw/bd_size_total_Business_demography_by_size_class.tsv.gz"
)

modern_survival = load_eurostat_data(
    project_root / "data/raw/bd_size_Y1_Y2_Y3.tsv.gz"
)
# %%
modern_demography_mask = (modern_demography["age"] == "TOTAL") & (modern_demography["indic_sbs"] == "ENT_BRTH_NR") & (modern_demography["year"] == 2021) & (modern_demography["sizeclas"] == "TOTAL")
births_2021 = modern_demography[modern_demography_mask].copy()
# %%
modern_survival_mask = (modern_survival["indic_sbs"] == "ENT_SRVL_NR") & (modern_survival["age"] == "Y3") & (modern_survival["year"] == 2024) & (modern_survival["sizeclas"] == "TOTAL")
survivors_2024 = modern_survival[modern_survival_mask].copy()
# %%
official_y3_mask = (modern_survival["indic_sbs"] == "ENT_SRVLR_BRTH_PC") & (modern_survival["age"] == "Y3") & (modern_survival["year"] == 2024) & (modern_survival["sizeclas"] == "TOTAL")
official_y3_2024 = modern_survival[official_y3_mask].copy()
# %%
births_for_check = births_2021[
    ["geo", "nace_r2", "value"]].rename(columns={"value": "births_2021_count"})

survivors_for_check = survivors_2024[
    ["geo", "nace_r2", "value"]].rename(columns={"value": "survivors_2024_count"})

official_for_check = official_y3_2024[
    ["geo", "nace_r2", "value"]].rename(columns={"value": "official_y3"})
# %%
y3_check = pd.merge(births_for_check, survivors_for_check, on=["geo", "nace_r2"], how="outer", validate="one_to_one")
y3_check = pd.merge(y3_check, official_for_check, on=["geo", "nace_r2"], how="outer", validate="one_to_one")
# %%
valid_denominator_mask = y3_check["births_2021_count"] > 0
y3_check["reconstructed_y3"] = y3_check.loc[valid_denominator_mask, "survivors_2024_count"] / y3_check.loc[valid_denominator_mask, "births_2021_count"] * 100
# %%
y3_comparison = y3_check.dropna(
    subset=["official_y3", "reconstructed_y3"]).copy()
# %%
y3_comparison["difference"] = y3_comparison["official_y3"] - y3_comparison["reconstructed_y3"]
y3_comparison["abs_difference"] = y3_comparison["difference"].abs()
# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

y3_comparison.to_csv(
    diagnostics_dir / "y3_reconstruction_2024_comparison.csv",
    index=False,
)
# %%
survivors_mask = ((modern_survival["indic_sbs"] == "ENT_SRVL_NR")
    & (modern_survival["age"] == "Y3")
    & (modern_survival["sizeclas"] == "TOTAL")
    & (modern_survival["year"].isin([2021, 2022, 2023]))
)

survivors_2021_2023 = modern_survival[survivors_mask].copy()
# %%
historical_demography = load_eurostat_data(project_root / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz")
# %%
historical_demography_mask = (historical_demography["indic_sb"]== "V11920") & (historical_demography["sizeclas"] == "TOTAL") & (historical_demography["year"].isin([2018, 2019, 2020]))
historical_births = historical_demography[historical_demography_mask].copy()
# %%
historical_births['survival_year'] = historical_births['year'] + 3
# %%
historical_births_for_check = historical_births[["geo", "nace_r2", "year", "survival_year", "value"]].rename(columns={"year": "birth_year", "value": "births_count"})
# %%
historical_births_for_check = historical_births_for_check.rename(columns={"survival_year": "year"})
# %%
survivors_for_reconstruction = survivors_2021_2023[["geo", "nace_r2", "year", "value"]].rename(columns={"value": "survivors_count"})
y3_reconstruction = pd.merge(historical_births_for_check, survivors_for_reconstruction, on=["geo", "nace_r2", "year"], how="outer", validate="one_to_one")
# %%
reconstructed_y3_mask = y3_reconstruction["births_count"] > 0
reconstructed_y3 = y3_reconstruction.loc[reconstructed_y3_mask].copy()
# %%
reconstructed_y3["reconstructed_y3"] = reconstructed_y3["survivors_count"] / reconstructed_y3["births_count"] * 100

# %%
reconstructed_y3_mask2 = (reconstructed_y3["reconstructed_y3"] < 0) | (reconstructed_y3["reconstructed_y3"] > 100)
reconstructed_y3.loc[reconstructed_y3_mask2,
                     ['geo', 'nace_r2', 'year', 'births_count', 'survivors_count', 'reconstructed_y3']]
# %%
official_y3_mask = (modern_survival["indic_sbs"] == "ENT_SRVLR_BRTH_PC") & (modern_survival["age"] == "Y3") & (modern_survival["sizeclas"] == "TOTAL") & (modern_survival["year"].isin([2021, 2022, 2023]))
official_y3 = modern_survival[official_y3_mask].copy()
available_official_y3 = official_y3.dropna(subset=["value"])
# %%
official_for_reconstruction = available_official_y3[
    ["geo", "nace_r2", "year", "value"]
].rename(columns={"value": "official_y3"})

y3_historical_comparison = reconstructed_y3.merge(
    official_for_reconstruction,
    on=["geo", "nace_r2", "year"],
    how="inner",
    validate="one_to_one",
).dropna(subset=["reconstructed_y3", "official_y3"])

y3_historical_comparison["abs_difference"] = (
    y3_historical_comparison["reconstructed_y3"]
    - y3_historical_comparison["official_y3"]
).abs()

# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

y3_historical_comparison.to_csv(
    diagnostics_dir / "y3_reconstruction_2021_2023_comparison.csv",
    index=False,
)