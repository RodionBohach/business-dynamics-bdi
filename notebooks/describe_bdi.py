# %%
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
project_root = Path(__file__).resolve().parents[1]

bdi_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)
# %%
bdi_summary_year = bdi_panel.groupby('year')['bdi_zscore'].agg(count = 'count', mean = 'mean', median = 'median', std = 'std').reset_index()
# %%
bdi_summary_country = bdi_panel.groupby('geo')['bdi_zscore'].agg(count = 'count', mean = 'mean', median = 'median', std = 'std').reset_index().sort_values(by='mean', ascending=False)
# %%
bdi_summary_nace = bdi_panel.groupby('nace_r2')['bdi_zscore'].agg(count = 'count', mean = 'mean', median = 'median', std = 'std').reset_index().sort_values(by='mean', ascending=False)

# %%
columns_to_corr = bdi_panel[['birth_rate', 'death_rate', 'survival_3y', 'high_growth_share']].dropna()
spearman_corr = columns_to_corr.corr(method = 'spearman')
# %%
descriptive_dir = project_root / "outputs/descriptive"
descriptive_dir.mkdir(parents=True, exist_ok=True)

bdi_summary_year.to_csv(descriptive_dir / 'bdi_summary_year.csv', index=False)
bdi_summary_country.to_csv(descriptive_dir / 'bdi_summary_country.csv', index=False)
bdi_summary_nace.to_csv(descriptive_dir / 'bdi_summary_nace.csv', index=False)
spearman_corr.to_csv(descriptive_dir / 'spearman_corr.csv', index=True)
# %%
figures_dir = project_root / "outputs/figures"
figures_dir.mkdir(parents=True, exist_ok=True)
plt.plot( bdi_summary_year['year'], bdi_summary_year['mean'], label="Mean")
plt.plot(bdi_summary_year['year'], bdi_summary_year['median'], label = "Median")
plt.legend()
plt.title("Mean and median BDI, 2013–2020")
plt.xlabel("Year")
plt.ylabel("BDI (z-score composite)")
plt.axhline(y=0, color='gray', linestyle = '--')
plt.savefig(figures_dir / "bdi_year_trend.png", dpi=300, bbox_inches="tight")
plt.show()
# %%

plt.figure()
plt.barh(bdi_summary_country['geo'], bdi_summary_country['mean'])
plt.gca().invert_yaxis()
plt.axvline(x=0, color='gray', linestyle = '--')
plt.xlabel("Mean BDI")
plt.ylabel("Country")
plt.title("Mean BDI by country, 2013–2020")
plt.savefig(figures_dir/ "bdi_country_mean.png", dpi=300, bbox_inches="tight")
plt.show()

# %%
plt.figure()
plt.barh(bdi_summary_nace['nace_r2'], bdi_summary_nace['mean'])
plt.gca().invert_yaxis()
plt.axvline(x=0, color='gray', linestyle = '--')
plt.xlabel("Mean BDI")
plt.ylabel("NACE section")
plt.title("Mean BDI by NACE section, 2013–2020")
plt.savefig(figures_dir/ "bdi_nace_mean.png", dpi=300, bbox_inches="tight")
plt.show()
# %%
plt.figure()
plt.hist(bdi_panel['bdi_zscore'].dropna(), bins=30,edgecolor='black', alpha=0.7)
plt.xlabel("BDI (z-score composite)")
plt.ylabel("Number of observations")
plt.title("Distribution of BDI, 2013–2020")
plt.savefig(figures_dir/ "bdi_distribution.png", dpi=300, bbox_inches="tight")
plt.show()
# %%
