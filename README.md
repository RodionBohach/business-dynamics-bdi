# business-dynamics-bdi

## Copyright and permissions

This repository is publicly available as a reproducible appendix
to a bachelor's thesis. Public availability does not grant permission
to reuse, modify, or redistribute the original code or documentation.

Copyright © 2026 Rodion Bohach. All rights reserved.
See LICENSE for details. Requests for permission can be submitted
through GitHub Issues.

Eurostat data and third-party dependencies remain subject to their
respective terms.

## Project overview

This repository contains the Python analysis for a bachelor's thesis
using an author-developed composite indicator and Business Intelligence.

The Business Development Index (BDI) summarizes the level and balance
of business formation, survival and high growth in a country–industry
observation. Changes in this score are analysed over time using
fixed reference parameters.

The historical panel covers 20 countries, 12 NACE sections and
2013–2020, with 1,920 country–industry–year observations.

The selected BDI specification combines:
- enterprise birth rate;
- three-year enterprise survival rate;
- high-growth enterprise share.

There are 1,918 observations with complete components.
NO/D/2020 is additionally excluded from the selected calculation
because of documented data-quality concerns, leaving 1,917 observations.

NO/D/2013–2019 is retained with a quality caveat. A sensitivity
analysis excludes the full historical NO/D series.

Death rate and churn are contextual indicators, not components
of the selected BDI.

Power BI reporting is planned separately.

## Selected BDI methodology

Original component values are preserved.

For the selected historical index, component values above their
99.9th percentile are capped at that percentile. Lower-tail values
are not increased. Thresholds are estimated on the historical
reference sample and fixed across years.

Means and population standard deviations are calculated after
this treatment. Each component is transformed as:

r_j = 100 + 10 * (x_j_analytical - mean_j) / std_j

The reference parameters are fixed across years.
A normalized component value of 100 represents its reference mean,
not an economic target.

The three components receive equal formal weights.
The MPI-style aggregation is:

M = arithmetic mean of normalized components
S = population standard deviation across those components
Penalty = S² / M
BDI = M - Penalty

The index evaluates the level and balance of the three selected
directions. It reduces compensation between components but does
not eliminate it.

The penalty measures imbalance within an observation, not volatility
over time. BDI combines different populations and time windows;
it does not follow one cohort or predict an individual firm's survival.

The selected output column is `bdi_mpi`.
The panel also retains `bdi_zscore` and `bdi_minmax` as legacy
four-component alternatives. These columns must not be confused
with the selected specification.

Local monotonicity is checked on the observed analytical sample.
This does not establish monotonicity for every possible future profile.

## Historical and modern analysis

Historical S1/S2/S3 comparisons use a common sample and the same
construction rules, with a separate reference distribution for
each survival horizon.

Modern analysis is conducted separately:
- S1: 2022–2024;
- S2: 2023–2024;
- S3: 2024.

The modern index uses fixed reference parameters estimated on
237 common country–industry observations in 2024.
Temporal summaries use a constant set of pairs within each version.

Historical and modern index levels are not directly comparable.
Fixed normalization alone does not resolve source-methodology breaks.

Country summaries are unweighted averages of available
country–industry–year scores, not official national aggregates.
Historical temporal summaries additionally use a balanced sample
of 237 pairs, or 1,896 observations.

## Environment setup

Run commands from the repository root.
The analysis was developed with Python 3.13.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Required source files

Place the following Eurostat extracts in `data/raw/`.
Raw files are not included in the repository.

- `bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz`
- `bd_9pm_r2_High_growth_enterprises.tsv.gz`
- `bd_size_total_Business_demography_by_size_class.tsv.gz`
- `bd_size_Y1_Y2_Y3.tsv.gz`
- `bd_hg_High_growth_enterprises_and_related_employment.tsv.gz`
- `nama_10_a64_Gross_value_added_and_income.tsv.gz`
- `nama_10_a64_e_Employment_by_detailed_industry.tsv.gz`
- `nama_10_a64_p5_Capital_formation_by_industry.tsv.gz`
- `bd_9bd_sz_cl_r2_survival_employment_growth_Y1_Y2_Y3.tsv.gz`
- `bd_size_survival_employment_growth_Y1_Y2_Y3.tsv.gz`

Filenames identify local extracts. Selected dimensions, download dates
and file hashes are documented in `docs/data_sources.md` and
`docs/raw_sources_manifest.json`.

Later Eurostat revisions may change results.

## Execution order

### Check sources and build the historical panel

```bash
python notebooks/check_eurostat_loader.py
python notebooks/document_raw_sources.py
python src/data/build_y_panel.py
python src/data/build_x_panel.py
python src/data/merge_panels.py
python src/index/build_bdi.py
```

### Run audits and selected descriptive comparisons

```bash
python notebooks/audit_modern_y.py
python notebooks/audit_survival_horizons.py
python notebooks/describe_bdi.py
python notebooks/compare_survival_horizons.py
python notebooks/build_modern_bdi_snapshot.py
```

### Prepare and estimate selected models

```bash
python notebooks/prepare_models.py
python src/model/fit_baseline.py
python src/model/fit_fixed_effects.py
python notebooks/compare_models.py
```

The selected models use `bdi_mpi`.
Model output filenames include `mpi`.

The FE analysis compares pair and country clustering, the MPI score
with its unpenalized mean, and sensitivity to selected observations.
These estimation-sample checks retain the original index values.

### Supporting and preliminary experiments

```bash
python notebooks/diagnose_bdi.py
python notebooks/check_y3_reconstruction.py
python notebooks/check_historical_2012_coverage.py
python notebooks/compare_death_rate_role.py
python notebooks/compare_growth_components.py
python notebooks/compare_bdi_ampi.py
python notebooks/build_modern_bdi_snapshot_legacy.py
```

These scripts document source audits and construction choices.
Some intentionally calculate earlier arithmetic or four-component
alternatives. Their results are not automatically results of the
selected MPI specification.

The legacy modern script also preserves the exploratory C/J
preference scenarios.

## Execution notes

Run `.py` files as complete scripts. Paths use `__file__`;
interactive cells may require separate path setup.

Supporting scripts may display plots and require their windows
to be closed before execution continues.

FE summaries may emit a warning about a rank-deficient covariance
matrix of constraints. The omnibus robust test of all coefficients,
including fixed effects, is not interpreted.

Model summaries contain execution timestamps.

Regression estimates describe conditional statistical associations,
not established causal effects. R-squared values from FE models
include the fixed effects.

## Outputs and documentation

- `data/processed/`: intermediate and audited tables.
- `data/final/`: analytical panels, selected BDI and model sample.
- `outputs/coverage/`: historical and modern coverage summaries.
- `outputs/descriptive/`: index summaries and component correlations.
- `outputs/diagnostics/`: audits, parameters and sensitivity analyses.
- `outputs/models/`: regression estimates and comparisons.
- `outputs/figures/`: exported figures; legacy figures remain until
  explicitly replaced during final report preparation.
- `docs/data_decisions.md`: methodological decisions.
- `docs/results_and_limitations.md`: interpretation and limitations;
  requires reconciliation with the selected MPI results before submission.

Selected historical descriptive outputs use the prefix `bdi_mpi`.
Selected modern outputs use `modern_mpi`.
Historical horizon-comparison outputs use `mpi_survival`.
Construction experiments are stored in
`outputs/diagnostics/bdi_ampi_experiment/`.

Earlier outputs are retained for traceability and must not be
presented as selected MPI results.

The final report and figures are being updated to the selected
specification. A complete sequential rerun is required after
the migration is finalized.