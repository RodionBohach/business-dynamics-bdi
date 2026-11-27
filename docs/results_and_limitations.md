# Results and limitations

## Analytical sample and selected index

BDI stands for Business Development Index. It summarizes the level
and balance of business formation, survival and high growth.

The historical panel covers 20 countries and 12 NACE sections
over 2013–2020, with 1,920 country–industry–year observations.

Two Romanian three-year survival values, J/2013 and N/2013,
were quarantined because they exceeded 100%.
NO/D/2020 was additionally excluded because of documented
data-quality concerns.

The selected BDI and model sample therefore contain
1,917 observations.

The three components are birth rate, three-year survival rate,
and high-growth enterprise share. Death rate and churn are
reported separately as context.

Original values are preserved. For index calculation, components
are upper-winsorized at their historical 99.9th percentiles.
This affects six values in six observations.
Lower-tail values are not increased.

Fixed historical means and population standard deviations,
calculated after treatment, define normalized scores:

r_j = 100 + 10 × (x_j_analytical − mean_j) / std_j

The selected aggregation is:

BDI = M − S² / M

M is the mean normalized component score; S is the population
standard deviation across components within an observation.

The penalty reflects imbalance between normalized achievements,
not volatility over time. A score of 100 is not a welfare target,
and an individual component's reference mean is not an economic norm.

## Historical descriptive findings

### Country and industry comparisons

The highest historical country means are:
- Netherlands: 105.311;
- Sweden: 103.556;
- Slovakia: 101.772.

The lowest are:
- Romania: 93.984;
- Germany: 94.807;
- Italy: 96.595.

Section J has the highest industry mean, 105.690,
followed by N, 103.450, and H, 101.857.
Section B has the lowest mean, 94.809.

These are unweighted averages of observation-level index scores,
not official national aggregates or comprehensive economic rankings.

Coverage is 96 observations per country except Norway with 95
and Romania with 94. Coverage counts accompany the summaries.

### Level and imbalance

The Netherlands combines a mean component level of 105.640
with a mean penalty of 0.329, giving mean BDI of 105.311.

Portugal has a mean level of 101.997 and a larger mean penalty
of 1.413, giving mean BDI of 100.583.

These figures illustrate the distinction between average component
achievement and imbalance. Country averages can conceal differences
between industries and years.

An average of individual MPI scores is not equivalent to MPI
calculated from aggregate country components.

### Time patterns on a balanced sample

Temporal summaries use 237 country–industry pairs present
in all eight years, giving 1,896 observations.

Mean BDI is 98.595 in 2013, reaches 100.381 in 2018,
and falls to 98.542 in 2020.

From 2019 to 2020:
- mean component level falls by approximately 1.630 points;
- mean penalty falls by approximately 0.035 points;
- mean BDI falls by approximately 1.594 points.

The lower penalty slightly offsets the decline in component level.
This decomposition does not establish the economic causes
of the component changes.

### Component relationships

On the selected sample, pooled Spearman correlations are:
- birth rate and survival: −0.3512;
- birth rate and high-growth share: 0.2461;
- survival and high-growth share: 0.0104.

The components are not interchangeable.
Low correlation alone does not validate their aggregation.

## Construction sensitivity

### Treatment of extreme values

Upper-only 99.9th-percentile treatment gives a Spearman correlation
of 0.999689 with untreated MPI on the same 1,917 observations.
The median absolute rank shift is 7 places; the maximum is 160.

No nonpositive local derivatives were detected at the treated
historical observations. Untreated MPI exhibited a violation
at PT/D/2016.

The treatment limits extreme influence while preserving observations.
It also creates saturation above each threshold.

High overall correlation does not mean that every individual
ranking is insensitive to processing choices.

### Retained historical Norway D observations

NO/D/2013–2019 is retained with an explicit source-quality caveat.

Excluding the entire historical NO/D pair and recalculating
reference parameters produces a rank correlation of 0.999996
on 1,910 common observations. The median rank shift is 1 place
and the maximum is 9.

This indicates limited influence on the other observations'
index rankings, not proof that the retained source values are correct.

### Survival horizons

Three MPI variants were compared on 1,915 common observations,
using one-, two- or three-year survival.

S1–S3 rank correlation is 0.894374; S2–S3 correlation is 0.942351.
Median absolute rank shifts are 113 and 66 places, respectively.
Maximum shifts are 1,690 and 1,674 places.

The survival horizon can therefore materially affect individual
positions even when overall correlations are high.

S3 remains the selected historical specification.
S1/S2 are alternative survival horizons, not fully one- or
two-year indices: high-growth retains its three-year window.

## Regression findings

### Pooled and fixed-effects estimates

Both selected models use 1,917 observations and four predictors:
investment intensity, labour share, log labour productivity,
and employment growth.

All pooled coefficients are positive.
After introducing country–industry and year fixed effects,
labour share and log labour productivity become negative.

Pooled and within-pair associations differ; the sign changes
do not identify the mechanisms behind them.

Pooled R-squared is approximately 0.098.
FE R-squared is approximately 0.729, including the fixed effects.
The latter is not the variation explained by the four X alone,
nor does it establish that this index is superior to alternatives.

### Country-clustered FE results

| Predictor | Coefficient | p-value | 95% interval |
|---|---:|---:|---|
| Investment intensity | 0.031375 | 0.065310 | [−0.002195; 0.064945] |
| Labour share | −0.139445 | 0.119895 | [−0.318670; 0.039780] |
| Log labour productivity | −2.428811 | 0.506811 | [−9.942141; 5.084520] |
| Employment growth | 0.088608 | 0.045243 | [0.002080; 0.175136] |

Coefficients are in BDI points per unit of the predictor.
Rates are recorded in percentage points; productivity is logged.

The positive employment-growth association is close to the
conventional 5% threshold and requires cautious interpretation.

Pair-clustered inference produces smaller p-values for several
predictors. Clustering choices are not selected by significance.

Country-clustered inference uses 20 clusters and remains approximate.
The omnibus robust test including all FE is not interpreted.

### Sensitivity and influence

The unpenalized mean-score FE model produces close coefficients.

Excluding PT/D/2016 or the full historical NO/D pair from estimation
also produces close coefficients. These checks keep index values
and reference parameters fixed.

The three observations with highest Cook's distance are
EE/D/2020, SE/D/2018 and SI/B/2014.

Excluding these three observations preserves coefficient signs.
However, the employment-growth coefficient changes from
0.088608 to 0.078824, and its p-value rises from 0.045243 to 0.072539.

Its significance at 5% is therefore not robust to this diagnostic
exclusion. The full 1,917-observation model remains the main model.

Cook's distance concerns the full OLS dummy-variable model.
It is not cluster-adjusted and is not an automatic deletion rule.

Within-predictor VIF values are approximately 1.03–1.61.
This diagnostic does not indicate substantial linear collinearity.

## Separate modern application

Modern MPI uses a separate reference sample of 237 common
country–industry observations in 2024.

The same construction rule is used, but modern thresholds,
means and standard deviations are estimated separately.
Historical and modern levels are not directly comparable.

Versions are calculated for:
- S1: 2022–2024;
- S2: 2023–2024;
- S3: 2024.

Earlier years with only 12 available survival observations
are not used for broad index comparisons.

In 2024, S1–S3 rank correlation is 0.866438 and S2–S3 is 0.921358.
Median rank shifts are 17 and 9 places.

The Netherlands has the highest country mean in all three versions.
Country coverage is 11 industries for Norway, 10 for Hungary,
and 12 for the other countries.

Balanced temporal summaries use 238 pairs for S1 and 237 for S2.
Mean S1 falls by approximately 0.958 points in 2024;
mean S2 falls by approximately 0.446 points.

These are descriptive changes under a fixed 2024 reference,
not causal estimates or real-time forecasts.
The 2024 reference is used retrospectively.

## Attempted reconstruction of Y3

For 2024, modern survivor and birth counts reproduced 492 available
official rates within approximately 0.005 percentage points,
consistent with rounding.

For 2021–2023, combining historical births with modern survivors
produced 23 rates above 100% and substantial discrepancies
against available official rates.

| Country | Comparable observations | Mean absolute difference, pp | Maximum, pp |
|---|---:|---:|---:|
| Finland | 45 | 10.087 | 83.788 |
| Iceland | 36 | 2.873 | 21.430 |
| Türkiye | 45 | 2.262 | 13.568 |

These extracts cannot be assumed to provide compatible cohort
numerators and denominators. The precise cause remains unresolved.

Reconstructed rates were not adopted.
This does not establish that reconstruction is impossible with
compatible revised data.

## Limitations

### Measurement and comparability

Results concern the selected countries, industries and periods.

National methodological changes, coverage differences and revisions
can affect comparisons. Fixed effects do not remove time-varying
statistical breaks. A plausible-looking series or absence of flags
does not establish comparability.

The retained historical NO/D observations and modern cohort
statistics require the documented quality caveats.

Monetary X are in current EUR, not inflation- or PPP-adjusted.
Labour share is not adjusted for self-employed labour.
Aggregate relationships do not establish firm-level relationships.

### Index assumptions

Component selection, positive directions, equal formal weights,
normalization and the penalty are author-defined choices.

Higher birth rate is treated as greater formation intensity,
not proof of greater welfare or productivity.

Equal formal weights do not guarantee equal statistical influence.

The penalty favors balanced normalized achievement.
This preference is not a universal economic law.
Components cover different populations and time windows.

The 99.9th percentile is not an official benchmark.
Local monotonicity checks do not guarantee global monotonicity.
Future data require validation against the fixed specification.

### Econometric interpretation

Regressions estimate conditional associations, not causal effects.
Time-varying confounding, reverse causality and measurement error remain.

Employment growth may be jointly determined with business outcomes
and is conceptually related to employment-based high-growth status.

Country clustering does not accommodate cross-country dependence,
and inference with 20 clusters remains approximate.

Predictive performance has not been evaluated.

## Overall assessment and project implication

The selected BDI provides a transparent summary of three directions
of enterprise development, with a separate imbalance penalty.

Its practical contribution is the joint presentation of:
- overall score;
- average component level;
- imbalance penalty;
- underlying components and data-quality information.

Historical descriptive differences are substantial, while regression
evidence is exploratory and sensitive to inference and influence checks.

A proposed Power BI implementation should expose the decomposition,
coverage and separate historical/modern reference bases.
It should not present BDI as a probability of business success
or a definitive ranking of national economic quality.

Figures and the final Word report remain to be updated.
Earlier four-component results are construction-history evidence,
not the selected findings.