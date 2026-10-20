# Results and limitations

## Analytical sample

The main panel covers 20 countries and 12 NACE sections over 2013–2020, giving 1,920 country–industry–year observations. BDI is available for 1,918 observations.

Two three-year survival rates for Romania (sections J and N, 2013) exceeded 100%. Their original values were retained, while their analytical values were set to missing. No partial-component BDI was calculated.

## Descriptive results

### Time patterns

The mean z-score BDI increased from −0.087 in 2013 to 0.095 in 2018, before declining to 0.035 in 2019 and −0.046 in 2020. The median followed a broadly similar pattern.

The cross-sectional standard deviation was highest in 2020 (0.505), indicating greater dispersion across country–industry observations in that year. These descriptive patterns do not establish their causes.

### Country and industry patterns

The Netherlands, Sweden, and France had the highest mean BDI values over the sample period. Romania and Germany had the lowest means.

NACE section J had the highest industry mean, while sections G and I had the lowest. Section D displayed the greatest dispersion.

These summaries assign equal weight to each available country–industry–year observation. They are not weighted by employment, enterprise counts, or economic output, and should not be interpreted as comprehensive rankings of national economies.

### Component relationships

Across the 1,918 complete observations, the pooled Spearman correlation between birth and death rates was 0.632. Death rates and three-year survival rates were negatively correlated (−0.585), as were birth rates and survival rates (−0.349).

High-growth shares and survival rates showed little pooled monotonic association (0.009). These correlations combine differences across countries, industries, and years and do not establish causal relationships.

## Regression results

### Pooled OLS and fixed effects

Both models use the same 1,918 observations and four predictors: investment intensity, labour share, log labour productivity, and employment growth.

All four pooled OLS coefficients were positive. After introducing country × NACE and year fixed effects, labour share and log labour productivity became negative, while investment intensity and employment growth remained positive.

The fixed-effects model estimates associations using changes within country–industry pairs, controlling for time-invariant pair characteristics and common year effects. The sign changes indicate that pooled and within-pair associations differ; they do not establish the mechanisms behind these differences.

Pooled OLS had an R-squared of 0.165. The fixed-effects model had an R-squared of 0.674, including the contribution of the fixed effects. The latter should not be interpreted as variation explained by the four economic predictors alone.

### Uncertainty and clustering

With country × NACE clustering, all four fixed-effects coefficients had t-based p-values below 0.05. With country-level clustering, standard errors increased:

| Predictor | Coefficient | Country-clustered p-value |
|---|---:|---:|
| Investment intensity | 0.00257 | 0.0695 |
| Labour share | −0.01256 | 0.0613 |
| Log labour productivity | −0.30664 | 0.2409 |
| Employment growth | 0.00783 | 0.0497 |

The coefficients were unchanged by the clustering choice, but statistical significance was sensitive to it. The employment-growth result was borderline, with a confidence interval whose lower bound was close to zero.

Country clustering allows dependence across industries and years within a country. However, inference based on only 20 country clusters remains approximate, and dependence across countries is not accommodated by this clustering scheme.

### Sensitivity checks

Excluding PT/D/2016, NO/D/2020, and RO/M/2013 from estimation preserved all four coefficient signs and produced estimates close to the baseline fixed-effects results. This check used country × NACE clustering and unchanged BDI values.

Replacing z-score BDI with min–max BDI also preserved all four coefficient signs. Under country-level clustering, however, all min–max model confidence intervals included zero. Raw coefficient magnitudes are not directly comparable across the two BDI scales.

Overall, the examined specifications show consistent coefficient directions, but do not provide consistently strong statistical evidence across inference and normalization choices.

## Limitations

### Data coverage and comparability

The findings apply to the selected 20 countries, 12 NACE sections, and 2013–2020 period. They cannot automatically be generalized to other countries, industries, or periods.

The modern-data audit found only 12 complete observations out of 240 in each year from 2021 to 2023, compared with 238 in 2024. The main analysis therefore does not provide a continuous assessment through 2024.

Historical data may contain changes in definitions, statistical coverage, and reporting practices. Fixed effects do not necessarily remove the consequences of time-varying methodological breaks.

Extreme observations were checked against the downloaded source data, but arithmetic consistency does not establish economic comparability or explain their causes. Source flags were retained during preparation but were not systematically used to exclude provisional or otherwise flagged observations.

### Index construction

BDI reflects four selected components, their assigned directions, equal weights, and the chosen aggregation method. These are methodological choices rather than uniquely determined properties of entrepreneurial dynamics.

Treating the death rate as a negative component is a substantive assumption. Enterprise exits can also form part of economic restructuring, so a higher BDI should not automatically be interpreted as higher welfare or better economic performance.

Normalization parameters were estimated using the pooled complete-case sample. The index therefore measures relative positions within this reference sample. Its values are not directly transferable to another period or sample without an explicit normalization strategy.

The sensitivity analysis examined selected scenarios rather than every possible weighting, component selection, or treatment of extreme values.

### Measurement of explanatory variables

Monetary variables are measured in current EUR. Labour productivity is nominal and is not adjusted for inflation or purchasing-power differences. Taking its logarithm does not remove these limitations.

Labour share is measured as employee compensation divided by gross value added and is not adjusted for the labour income of self-employed persons.

Country–industry aggregation can conceal differences between individual enterprises. The estimated relationships should not be interpreted as firm-level relationships.

### Econometric interpretation

The regressions describe conditional associations, not causal effects. Fixed effects account for time-invariant country–industry characteristics and common year effects, but do not eliminate time-varying confounding, reverse causality, or measurement error.

Contemporaneous employment growth may be jointly determined with entrepreneurial dynamics and is conceptually related to the employment-based high-growth component of BDI.

Statistical inference is sensitive to the clustering level. Country clustering uses only 20 clusters and does not address cross-country error dependence.

The reported results are in-sample estimates. Out-of-sample predictive performance has not been evaluated.

## Overall conclusions

A reproducible workflow was developed to transform Eurostat data into an analytical country–industry panel, construct BDI, and examine its descriptive patterns and economic associations.

The descriptive analysis identified differences across countries, industries, and years. Mean BDI increased up to 2018 and declined in 2019–2020 within the selected sample. These patterns do not establish their underlying causes.

Z-score BDI rankings were more stable than min–max rankings under the examined normalization-reference exclusions. This supports using z-score BDI as the main specification, while retaining min–max as an alternative.

Fixed-effects estimates consistently associated investment intensity and employment growth positively with BDI, and labour share and log labour productivity negatively, across the examined exclusion and normalization specifications. However, statistical significance was sensitive to the clustering level and BDI normalization. The findings therefore provide exploratory evidence of associations rather than firm evidence of causal effects.

The main contribution is a transparent framework for measuring and exploring entrepreneurial dynamics. The resulting index and visualizations should be interpreted alongside component values, data-quality information, and the stated methodological limitations.