# Data decisions
Planned coverage: 2013–2024. The currently implemented and validated panel covers the historical period 2013–2020. Modern data for 2021–2024 will be harmonized and assessed for comparability before inclusion.
## 1. Reproducible data preparation

Raw Eurostat files are preserved without manual modifications.
A shared Python loader reads all eight TSV.gz exports and converts
them into long format.

Dimension names are extracted from source headers because datasets
have different structures. Numeric values and flags are stored
separately, while the original cell is retained in `value_raw`.

Unexpected numeric tokens raise an error rather than silently
becoming missing values.

**Ete:** `431 b` becomes numeric value `431` and
flag `b`; `: p` becomes a missing numeric value while preserving
flag `p`. Missing observations can also carry source information.

## 2. Historical analytical sample

The main sample is:

- 20 countries;
- 12 NACE sections;
- 2013–2020.

The unit of analysis is country × NACE × year.

The resulting grid contains 1,920 observations and 7,680
component-level records. Before quarantine, all four components
are available and no duplicate analytical keys are present.

The period follows the prior coverage audit: high-growth data
were unavailable for the candidate sample in 2010–2011.
The earlier-period audit still needs to be reproduced in this pipeline.

**Ptd:** a year column in a source file does not imply
that the indicator has usable values for that year.

## 3. Component mapping

| Eurostat code | Component |
|---|---|
| V97020 | birth_rate |
| V97030 | death_rate |
| V97043 | survival_3y |
| V97460 | high_growth_share |

Rates are preserved in their original form during data preparation.
The negative direction of death rate will be applied during
BDI construction.

**Ptd:** source-data preparation and index construction
are separate stages, making transformations easier to audit.

## 4. Survival quarantine

Two observations are quarantined:

| geo | NACE | year | Original value |
|---|---|---:|---:|
| RO | J | 2013 | 132.56 |
| RO | N | 2013 | 105.36 |

The prior review identified concerns about coverage changes and
cohort comparability. The rule applies specifically to these
observations; it is not an automatic exclusion of all rates above 100.

Original values and flags are retained. Only the analytical survival
values are set to missing, and the affected records are marked
with `quarantined=True`.

**Ptd:** a value can be arithmetically consistent with
source counts but unsuitable for comparison across cohorts.

Supporting metadata references will be added.

## 5. Validation and outputs

The exported historical Y-panel contains:

- 1,920 rows with unique country × NACE × year keys;
- two missing values, both in survival_3y;
- 1,918 complete observations.

All rows are retained; quarantine does not delete observations.

Checks before export cover panel size, duplicate keys, and missing
values. The exported CSV was read back to verify its structure.

Outputs:

- `data/processed/Y_main_long.csv`: source values, flags, and quarantine;
- `data/final/Y_panel.csv`: analytical panel.

- built a reusable parser for eight differently
structured Eurostat exports and an auditable panel pipeline that
preserves source information and checks expected results.

## Modern Y coverage audit

For the same 20 countries and 12 NACE sections, official rates
provide complete four-component observations for:

- 2021: 12/240 (5%);
- 2022: 12/240 (5%);
- 2023: 12/240 (5%);
- 2024: 238/240 (99.17%).

The main limitation is missing official Y3 survival rates
in 2021–2023. Missing values are preserved without imputation.

The main analytical sample remains 2013–2020.
Year 2024 is a candidate for a separate modern snapshot,
subject to methodological comparability checks.

Coverage results are exported to `outputs/coverage/`.

## Historical–modern comparability

Eurostat indicates that data from 2021 are comparable with earlier
years unless a break in series is reported. The EBS transition
alone does not establish a break for every country.

France explicitly reports that data from 2021 are generally not
comparable with previous years. Sweden changed its statistical
unit in 2022, while preserving legal units for selected survival
cohorts.

Therefore, historical and modern data are not automatically
treated as one continuous panel. The main sample remains
2013–2020; 2024 remains a candidate for a separate snapshot.

Germany also reports a statistical-unit change in 2018 and a
register-threshold change in 2019. These limitations within the
historical sample will be considered in robustness analysis.

The precise cause of missing official Y3 rates in 2021–2023
has not been independently established.

Sources:
- [Eurostat general metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/bd_sims.htm)
- [France](https://ec.europa.eu/eurostat/cache/metadata/EN/bd_simsbd21_fr.htm)
- [Sweden](https://ec.europa.eu/eurostat/cache/metadata/en/bd_simsbd21_se.htm)
- [Germany](https://ec.europa.eu/eurostat/cache/metadata/EN/bd_simsbd21_de.htm)
