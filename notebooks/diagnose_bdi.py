# %%
import pandas as pd 
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
bdi_panel = pd.read_csv(project_root / "data/final/BDI_panel.csv")
# %%
top_birhts = bdi_panel.nlargest(5,'birth_rate')[["geo", "nace_r2", "year", "birth_rate", "bdi_zscore", "bdi_minmax"]]
top_death = bdi_panel.nlargest(5, 'death_rate')[["geo", "nace_r2", "year", "death_rate", "bdi_zscore", "bdi_minmax"]]
top_high_growth = bdi_panel.nlargest(5, 'high_growth_share')[["geo", "nace_r2", "year", "high_growth_share", "bdi_zscore", "bdi_minmax"]]
# %%
bottom_survival = bdi_panel.nsmallest(5, "survival_3y")[["geo", "nace_r2", "year", "survival_3y", "bdi_zscore", "bdi_minmax"]]
# %%
norway_mask = (
    (bdi_panel["geo"] == "NO")
    & (bdi_panel["nace_r2"] == "D")
    & (bdi_panel["year"] == 2020)
)
# %%
y_source = pd.read_csv(project_root / "data/processed/Y_main_long.csv")
source_mask = (
    (y_source["geo"] == "NO")
    & (y_source["nace_r2"] == "D")
    & (y_source["year"] == 2020)
)
# %%
norway_history_mask = (
    (y_source["geo"] == "NO")
    & (y_source["nace_r2"] == "D")
)
# %%
import sys

sys.path.insert(0, str(project_root / "src"))
from data.load_eurostat import load_eurostat_data

historical_demography = load_eurostat_data(
    project_root / "data/raw/bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"
)
# %%
norway_d_active_mask = (
    (historical_demography["geo"] == "NO")
    & (historical_demography["nace_r2"] == "D")
    & (historical_demography["indic_sb"] == "V11910")
    & (historical_demography["sizeclas"] == "TOTAL")
)
# %%
norway_d_active_history = historical_demography.loc[
    norway_d_active_mask,
    ["year", "value_raw", "value", "flag"]
].sort_values("year").copy()
# %%
diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

norway_d_active_history.to_csv(
    diagnostics_dir / "norway_d_active_history.csv",
    index=False,
)
# %%
y_source_mask = (
    (y_source["geo"] == "PT")
    & (y_source["nace_r2"] == "D")
    & (y_source["year"] == 2016)
)
# %%
portugal_counts_mask = (
    (historical_demography["geo"] == "PT")
    & (historical_demography["nace_r2"] == "D")
    & (historical_demography["year"].isin([2015, 2016, 2017]))
    & (historical_demography["sizeclas"] == "TOTAL")
    & (historical_demography["indic_sb"].isin(["V11910", "V11920", "V97020"]))
)
# %%
portugal_birth_audit = historical_demography.loc[
    portugal_counts_mask,
    ["year", "indic_sb", "value_raw", "value", "flag"]
].sort_values(["year", "indic_sb"]).copy()

portugal_birth_audit.to_csv(
    diagnostics_dir / "portugal_d_birth_audit.csv",
    index=False,
)
# %%
romania_counts_mask = (
    (historical_demography['geo']=="RO")
    & (historical_demography['nace_r2']=='M')
    & (historical_demography["year"].isin( [2012, 2013, 2014]))
    & (historical_demography['sizeclas']=='TOTAL')
    & (historical_demography['indic_sb'].isin(["V11910", "V11930", "V97030"]))
)
# %%
romania_death_audit = historical_demography.loc[
    romania_counts_mask,
    ["year", "indic_sb", "value_raw", "value", "flag"]
].sort_values(["year", "indic_sb"]).copy()

romania_death_audit.to_csv(
    diagnostics_dir / "romania_m_death_audit.csv",
    index=False,
)
# %%
sensitivity_exclusion_mask = (
    (
        (bdi_panel["geo"] == "NO")
        & (bdi_panel["nace_r2"] == "D")
        & (bdi_panel["year"] == 2020)
    )
    | (
        (bdi_panel["geo"] == "PT")
        & (bdi_panel["nace_r2"] == "D")
        & (bdi_panel["year"] == 2016)
    )
    | (
        (bdi_panel["geo"] == "RO")
        & (bdi_panel["nace_r2"] == "M")
        & (bdi_panel["year"] == 2013)
    )
)
# %%
components = [
    "birth_rate",
    "death_rate",
    "survival_3y",
    "high_growth_share",
]

sensitivity_reference = bdi_panel.loc[
    bdi_panel["bdi_complete"] & ~sensitivity_exclusion_mask,
    components,
].copy()
# %%
sensitivity_means = sensitivity_reference.mean()
sensitivity_stds = sensitivity_reference.std(ddof=0)
# %%
directions = pd.Series({
    "birth_rate": 1,
    "death_rate": -1,
    "survival_3y": 1,
    "high_growth_share": 1,
})

sensitivity_z_scores = (
    (bdi_panel[components] - sensitivity_means)
    / sensitivity_stds
) * directions
# %%
bdi_panel["bdi_zscore_sensitivity"] = sensitivity_z_scores.mean(
    axis=1,
    skipna=False,
)
# %%
comparison_mask = (
    bdi_panel["bdi_complete"] & ~sensitivity_exclusion_mask
)

bdi_panel.loc[
    comparison_mask,
    ["bdi_zscore", "bdi_zscore_sensitivity"],
].corr(method="spearman")
# %%
rank_comparison = bdi_panel.loc[
    comparison_mask,
    ["geo", "nace_r2", "year", "bdi_zscore", "bdi_zscore_sensitivity"],
].copy()

rank_comparison["rank_baseline"] = rank_comparison["bdi_zscore"].rank(
    ascending=False, method="average"
)
rank_comparison["rank_sensitivity"] = rank_comparison[
    "bdi_zscore_sensitivity"
].rank(ascending=False, method="average")

rank_comparison["rank_shift_abs"] = (
    rank_comparison["rank_sensitivity"]
    - rank_comparison["rank_baseline"]
).abs()
# %%
rank_comparison.to_csv(
    diagnostics_dir / "bdi_zscore_sensitivity_ranks.csv",
    index=False,
)
# %%
sensitivity_mins = sensitivity_reference.min()
sensitivity_maxs = sensitivity_reference.max()
sensitivity_ranges = sensitivity_maxs - sensitivity_mins
# %%
sensitivity_minmax_scores = (
    (bdi_panel[components] - sensitivity_mins)
    / sensitivity_ranges
)

sensitivity_minmax_directed = sensitivity_minmax_scores.copy()
sensitivity_minmax_directed["death_rate"] = (
    1 - sensitivity_minmax_scores["death_rate"]
)

bdi_panel["bdi_minmax_sensitivity"] = sensitivity_minmax_directed.mean(
    axis=1,
    skipna=False,
)
# %%
minmax_rank_comparison = bdi_panel.loc[
    comparison_mask,
    ["geo", "nace_r2", "year", "bdi_minmax", "bdi_minmax_sensitivity"],
].copy()

minmax_rank_comparison["rank_baseline"] = minmax_rank_comparison[
    "bdi_minmax"
].rank(ascending=False, method="average")

minmax_rank_comparison["rank_sensitivity"] = minmax_rank_comparison[
    "bdi_minmax_sensitivity"
].rank(ascending=False, method="average")

minmax_rank_comparison["rank_shift_abs"] = (
    minmax_rank_comparison["rank_sensitivity"]
    - minmax_rank_comparison["rank_baseline"]
).abs()
# %%
minmax_rank_comparison.to_csv(
    diagnostics_dir / "bdi_minmax_sensitivity_ranks.csv",
    index=False,
)
# %%
