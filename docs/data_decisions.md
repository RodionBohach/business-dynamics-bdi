# Data decisions

## 1. Current specification and status

BDI now stands for Business Development Index.

It is an author-developed composite measure of the level and
balance of business formation, survival and high growth in a
country–industry observation.

The selected historical specification uses:
- enterprise birth rate;
- three-year enterprise survival rate;
- high-growth enterprise share.

Death rate and churn are contextual indicators, not components
of the selected index.

The construction uses upper-tail winsorization, fixed historical
standardization and an MPI-style imbalance penalty.

The main index, model sample, pooled OLS, fixed-effects models,
descriptive tables, historical survival-horizon comparisons and
separate modern calculations have been updated.

The final report, figures and results-and-limitations document
still require reconciliation. A complete sequential rerun of the
updated pipeline remains outstanding.

Earlier four-component constructions and alternative aggregation
experiments are retained for traceability. Their results are not
the selected BDI results.

## 2. Sources and reproducible preparation

Raw Eurostat extracts are preserved without manual modifications.

A shared loader converts the ten local TSV.gz extracts to long
format. Dimension names are read from source headers.

Numeric values, flags and original cells are retained separately:
- `value`: numeric value;
- `flag`: source flag;
- `value_raw`: original cell.

Unexpected numeric tokens raise an error instead of silently
becoming missing values.

Source filenames, dimensions, download dates and SHA-256 hashes
are recorded in `docs/raw_sources_manifest.json`.
Dataset documentation is maintained in `docs/data_sources.md`.

The eight original extracts were downloaded on 8 October 2026.
The two additional survival/employment-growth extracts were
downloaded on 24 November 2026.

Later source revisions may change reproduced results.

## 3. Historical panel and coverage

The historical grid covers:
- 20 countries;
- 12 NACE sections;
- 2013–2020.

The analytical unit is country × NACE section × year.
The grid contains 1,920 unique observations.

The period is not extended to 2012: the coverage check found
missing high-growth shares for all 12 selected Finnish industries.
Some historical survival values in that year also failed the
0–100% range check.

Source data for 2012 are nevertheless used to calculate
employment growth for 2013.

Historical and modern data are not automatically joined into a
continuous comparable series.

## 4. Historical Y preparation

Historical mappings are:

| Eurostat code | Variable | Current role |
|---|---|---|
| V97020 | birth_rate | BDI component |
| V97030 | death_rate | Context |
| V97043 | survival_3y | BDI component |
| V97460 | high_growth_share | BDI component |

The Y-panel preserves 1,920 rows.

Two survival observations are quarantined:

| Country | NACE | Year | Original survival |
|---|---|---:|---:|
| RO | J | 2013 | 132.56% |
| RO | N | 2013 | 105.36% |

Original source values and flags are preserved.
Their analytical survival values are missing.

There are therefore 1,918 observations with complete selected
BDI components before the additional Norwegian quality exclusion.

The source audit and analytical transformation are separate:
published values are not silently overwritten.

## 5. Norway D: quality decision

NO/D/2020 is excluded from the selected historical BDI calculation.

The source audit found:
- active enterprises: 1,254 in 2019 and 9 in 2020;
- birth rate in 2020: 0%;
- three-year survival in 2020: 2.22%;
- high-growth share in 2020: 100%.

Statistics Norway reports insufficient basic data and/or breaks
affecting industry D up to and including 2020.

This supports a data-quality exclusion; it does not prove that
each individual published cell is an error.

NO/D/2013–2019 is retained with an explicit quality caveat:
- birth and death rates reproduce from source counts within
  rounding differences below 0.005 percentage points;
- the available series does not show a comparable collapse;
- high-growth and survival have not been fully reconstructed
  from their respective denominators.

Absence of flags and internal arithmetic consistency do not
establish complete source-data validity.

A sensitivity analysis excludes the entire historical NO/D pair.
On the same 1,910 remaining observations, recalculating reference
parameters produced:
- Spearman rank correlation: 0.999996;
- median absolute rank shift: 1 place;
- maximum absolute rank shift: 9 places.

A separate regression sensitivity check also found close
coefficients after removing the retained NO/D observations,
while holding index values fixed.

The selected historical reference sample contains 1,917 observations.

Source:
[Statistics Norway: Enterprises](https://www.ssb.no/en/virksomheter-foretak-og-regnskap/virksomheter-og-foretak/statistikk/foretak)

## 6. Treatment of extreme component values

Original values are preserved.

For index calculation, each selected component is capped at its
99.9th percentile in the complete historical reference sample,
after the quality exclusion. Quantiles use linear interpolation.

Lower-tail values are not increased.

Fixed historical upper thresholds are:
- birth rate: 30.13736%;
- three-year survival: 98.91912%;
- high-growth share: 24.98652%.

Full-precision parameters are saved and used in calculations.

This changes six component values in six observations.
PT/D/2016 remains in the analytical sample:
its original birth rate is 69.37%, while its index input is capped.

The treatment limits influence; it does not classify capped values
as erroneous or estimate their true values.

The percentile is an author-selected parameter, not an official
European target. Published composite-index methods provide
precedent for winsorization, but do not prescribe this exact rule.

Compared with untreated MPI on the same 1,917 observations:
- Spearman rank correlation: 0.999689;
- median absolute rank shift: 7 places;
- maximum absolute rank shift: 160 places.

Two-sided alternatives were examined. The selected upper-only
rule intervenes less and does not artificially raise low inputs.

Source:
[WIPO: GII 2024 methodology, treatment of outliers](https://www.wipo.int/web-publications/global-innovation-index-2024/en/appendix-i-conceptual-and-measurement-framework-of-the-global-innovation-index.html)

## 7. Fixed standardization and MPI aggregation

Reference means and population standard deviations are calculated
after winsorization and fixed across historical years.

For component j:

r_j = 100 + 10 × (x_j_analytical − mean_j) / std_j

Standard deviations use ddof=0.
A component score of 100 represents its reference mean,
not an economic target.

The components receive equal formal weights.
This does not imply equal empirical influence or establish
an economic law about their relative importance.

For each observation:

M = arithmetic mean of the three normalized components
S = population standard deviation across the three components
Penalty = S² / M
BDI = M − Penalty

This is MPI-style aggregation with fixed historical standardization,
not the min–max-normalized AMPI alternatives examined earlier.

The penalty measures imbalance between normalized component scores,
not temporal volatility. Compensation is reduced, not eliminated.

All normalized values in the selected historical calculation
are positive. No nonpositive local derivatives were detected
at the treated observations.

This does not establish global monotonicity for every possible
future profile. New applications require validation.

Winsorization causes saturation above the thresholds:
further increases in raw inputs do not increase analytical inputs.

Methodological reference:
[Mazziotta and Pareto: methods for constructing composite indices](https://www.istat.it/en/files/2013/12/Rivista2013_Mazziotta_Pareto.pdf)

## 8. Interpretation

BDI summarizes three selected directions of enterprise development.
It does not measure:
- overall economic welfare;
- policy effectiveness;
- all aspects of business conditions;
- an individual firm's probability of success.

The components refer to different populations and time windows.
In particular, high-growth share concerns the relevant population
of enterprises with 10 or more employees and a three-year growth window.

The index is not a single-cohort lifecycle measure.

BDI is reported alongside its mean level, penalty and components.
Different component profiles can still produce equal final scores.

With fixed parameters:

change in BDI = change in mean level − change in penalty.

This is an accounting decomposition of the index, not a causal
explanation of economic change.

## 9. Economic predictors

The X-panel covers the historical 1,920-key grid.
The seven base economic variables have complete numeric coverage
in the selected source period.

Monetary inputs use current million EUR; employment inputs use
thousand persons.

| Variable | Formula |
|---|---|
| investment_intensity | GFCF / GVA × 100 |
| labour_share | Compensation / GVA × 100 |
| average_compensation | Compensation / Employees × 1,000 |
| value_added_ratio | GVA / Output × 100 |
| gfcf_per_employed | GFCF / Employment × 1,000 |
| labour_productivity | GVA / Employment × 1,000 |
| employment_growth | (Employment / previous-year Employment − 1) × 100 |
| net_operating_surplus_mixed_income_margin | B2A3N / Output × 100 |

Labour share is not adjusted for self-employed labour.
Labour productivity is nominal, not inflation- or PPP-adjusted.

Employment growth is calculated within sorted country–industry
groups with consecutive source years.

Negative GFCF values for BG/J/2015, BG/E/2016 and LV/D/2017
are retained and flagged. Their specific causes are not established.

The selected predictors are investment intensity, labour share,
log labour productivity and employment growth.

The MPI model sample contains 1,917 observations.
There are no additional exclusions due to missing predictors.

## 10. Regression specification and diagnostics

Pooled OLS is a descriptive benchmark.
The FE model includes country × industry and year fixed effects.

Country–industry clustering and country clustering are compared.
FE comparisons use t-based inference.
The current pooled model uses normal-based clustered inference.

Country clustering uses 20 clusters; inference remains approximate.
Coefficients describe conditional associations, not causal effects.

FE R-squared includes all fixed effects.
The omnibus robust test of all coefficients is not interpreted
because the constraint covariance matrix is rank deficient.

Within-predictor VIF values are approximately 1.03–1.61.

Main country-clustered MPI coefficients are:
- investment intensity: 0.031375, p = 0.065310;
- labour share: −0.139445, p = 0.119895;
- log labour productivity: −2.428811, p = 0.506811;
- employment growth: 0.088608, p = 0.045243.

The unpenalized mean-score alternative gives close coefficients.

Excluding PT/D/2016 or the full NO/D pair produces close estimates.
These checks hold index values and reference parameters fixed.

A diagnostic exclusion of the three observations with highest
Cook's distance preserves coefficient signs, but changes the
employment-growth p-value from 0.045243 to 0.072539.
Significance at 5% is therefore sensitive to this exclusion.

Cook's distance is a conventional diagnostic for the full OLS
dummy-variable model, not a cluster-adjusted influence measure.

Coefficients and intervals are also scaled by predictor standard
deviations after removing pair and year effects.
Their units are MPI points per within-standard-deviation increase in X.

## 11. Descriptive aggregation and dynamics

Country and industry summaries are unweighted averages of
observation-level index values.

An average of MPI scores is not the same as MPI calculated
from aggregated components.

Coverage counts accompany summaries.
Historical country coverage is 96 observations except
NO with 95 and RO with 94.

Historical temporal comparisons additionally use 237 pairs observed
in all eight years: 1,896 observations.

On this balanced sample, mean MPI peaks in 2018 at approximately
100.381 and declines by 1.594 points in 2020.
The decline reflects a lower mean component level, partly offset
by a smaller mean penalty. Causes are not inferred from this decomposition.

## 12. Survival-horizon comparison and cohort audit

Historical S1/S2/S3 MPI variants use the same 1,915 observations,
the selected processing rule and separate reference parameters
for each survival horizon.

Reference parameters for common components are identical across
the three comparison variants. Comparison S3 may differ slightly
from the main index because its reference sample is smaller.

No local monotonicity violations were detected.

Relative to S3:
- S1 Spearman correlation: 0.894374; median rank shift: 113;
- S2 Spearman correlation: 0.942351; median rank shift: 66.

These versions change only the survival horizon.
High-growth retains its three-year definition.

A separate raw-data audit aligns the same birth cohorts
at ages one, two and three. For cohorts 2012–2017,
1,440 complete trajectories were obtained.

AT/E/2012 increased from 78.77% at age one to 82.19% at age two,
then declined to 76.71% at age three.
Source values carried no flags; the cause remains unknown.
The trajectory is retained and marked.

## 13. Modern data and separate application

Audited modern survival coverage, out of 240 expected observations:

| Year | S1 | S2 | S3 |
|---|---:|---:|---:|
| 2021 | 12 | 12 | 12 |
| 2022 | 238 | 12 | 12 |
| 2023 | 240 | 237 | 12 |
| 2024 | 240 | 240 | 237 |

Out-of-range survival values are missing only in the analytical
column; source values and flags remain preserved.

The modern MPI uses a separate common 2024 reference sample of
237 observations. Upper thresholds, treated means and standard
deviations are estimated on that sample and fixed across modern years.

Calculated versions:
- S1 for 2022–2024;
- S2 for 2023–2024;
- S3 for 2024.

This is a retrospective reference scheme, not a real-time forecast.

Balanced temporal samples contain 238 pairs for S1 and 237 for S2.
The S3 snapshot contains 237 pairs.

No local monotonicity violations were detected at evaluated observations.

In the common 2024 snapshot:
- S1–S3 rank correlation: 0.866438;
- S2–S3 rank correlation: 0.921358;
- median absolute shifts: 17 and 9 places.

Country summaries cover 11 industries for NO, 10 for HU,
and 12 for other countries. They are not official national aggregates.

Modern and historical levels are not directly comparable.
Norway's historical warning is not automatically converted into
a blanket modern exclusion; modern cohort quality remains a caveat.

Sources:
- [Eurostat general metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/bd_sims.htm)
- [France](https://ec.europa.eu/eurostat/cache/metadata/EN/bd_simsbd21_fr.htm)
- [Sweden](https://ec.europa.eu/eurostat/cache/metadata/en/bd_simsbd21_se.htm)
- [Germany](https://ec.europa.eu/eurostat/cache/metadata/EN/bd_simsbd21_de.htm)

Matching codes and fixed normalization do not establish comparability.
Known national statistical changes, including within the historical
period, remain limitations.

## 14. Reconstruction and preliminary experiments

### Y3 reconstruction

A 2024 check using births and survivors reproduced 492 available
official survival rates within approximately 0.005 percentage points.

Combining historical births with modern survivors for 2021–2023
produced values above 100% and substantial discrepancies against
available official rates.

This cross-period reconstruction was not accepted for the main index.
The failure is documented; the precise incompatibility is not fully resolved.

### Growth component

High-growth share and survivor employment growth were compared
in a preliminary arithmetic-index experiment.

Their component correlations were low, and their definitions differ.
Survivor employment growth was not adopted as an interchangeable
replacement for high-growth share.

The earlier index-comparison numbers are not selected MPI results.

### Preference scenarios

The C/J scenario exercise uses a demonstration survival threshold
and illustrative two-criterion weights.

It is an exploratory decision-support example, not the selected BDI.

### Legacy constructions

Four-component z-score/min–max indices, death-rate comparisons
and alternative MPI/AMPI normalizations remain available as
construction-history and sensitivity evidence.

Their earlier provisional decisions do not override the specification
documented above.

## 15. Reproduction and remaining work

README.md contains the current execution order.

Selected historical outputs use `bdi_mpi`, FE outputs include
`mpi`, modern outputs use `modern_mpi`, and historical horizon
comparisons use `mpi_survival`.

The final sequential rerun, reconciliation of
`docs/results_and_limitations.md`, updated figures and final
Word report remain to be completed.

Forecasting is outside the current implementation.
Power BI is the planned reporting/project stage.

Previous decision notes are archived in:
`docs/archive/data_decisions_before_mpi_consolidation.md`.

The updated main pipeline was rerun sequentially in the existing
project environment without execution errors. Reported numerical
results matched the preceding runs. A clean-environment installation
has not been tested.
