
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

This repository contains the Python analysis for a bachelor's thesis on entrepreneurial dynamics using a composite index and Business Intelligence.

The main sample covers 20 countries, 12 NACE sections, and 2013–2020. It contains 1,920 country–industry–year observations, of which 1,918 have complete BDI components.

Power BI reporting is planned separately.

## Environment setup

Run commands from the repository root. The analysis was developed with Python 3.13.

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

Place the following downloaded Eurostat files in `data/raw/`. These files are not included in the repository.

- `bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz`
- `bd_9pm_r2_High_growth_enterprises.tsv.gz`
- `bd_size_total_Business_demography_by_size_class.tsv.gz`
- `bd_size_Y1_Y2_Y3.tsv.gz`
- `bd_hg_High_growth_enterprises_and_related_employment.tsv.gz`
- `nama_10_a64_Gross_value_added_and_income.tsv.gz`
- `nama_10_a64_e_Employment_by_detailed_industry.tsv.gz`
- `nama_10_a64_p5_Capital_formation_by_industry.tsv.gz`

The filenames identify the local extracts used in this analysis. Their selected dimensions and download dates must be documented to reproduce the same source snapshot; later Eurostat revisions may change results.

## Execution order

### Build the analytical panel and BDI

```bash
python src/data/build_y_panel.py
python src/data/build_x_panel.py
python src/data/merge_panels.py
python src/index/build_bdi.py
```

### Run audits and descriptive analysis

```bash
python notebooks/check_eurostat_loader.py
python notebooks/audit_modern_y.py
python notebooks/diagnose_bdi.py
python notebooks/describe_bdi.py
```

### Prepare and estimate models

```bash
python notebooks/prepare_models.py
python src/model/fit_baseline.py
python src/model/fit_fixed_effects.py
python notebooks/compare_models.py
```

These `.py` files should be run as complete scripts. Their project paths are resolved using `__file__`; running individual cells in an interactive kernel may require separate path setup.

Plot windows may need to be closed for execution to continue.

The fixed-effects summary may emit a warning about a rank-deficient covariance matrix of constraints. The omnibus robust F-test is not interpreted. Coefficient estimates and confidence intervals are reported separately.

Model summary text files contain execution timestamps, so rerunning scripts may change their date and time fields.

## Outputs and documentation

- `data/processed/`: intermediate analytical tables.
- `data/final/`: Y-panel, X-panel, analytical panel, BDI, and model sample.
- `outputs/coverage/`: modern-data coverage summaries.
- `outputs/descriptive/`: descriptive statistics and component correlations.
- `outputs/diagnostics/`: data, index, and predictor diagnostics.
- `outputs/models/`: regression estimates and model comparisons.
- `outputs/figures/`: exported figures.
- `docs/data_decisions.md`: methodological decisions.
- `docs/results_and_limitations.md`: draft interpretation of results and limitations.


Source datasets and local extract contents are documented in
[docs/data_sources.md](docs/data_sources.md) and
[docs/raw_sources_manifest.json](docs/raw_sources_manifest.json).
