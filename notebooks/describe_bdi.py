# %%
from pathlib import Path

import numpy as np
import pandas as pd


project_root = Path(__file__).resolve().parents[1]

bdi_panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

descriptive_dir = project_root / "outputs/descriptive"
descriptive_dir.mkdir(parents=True, exist_ok=True)

keys = ["geo", "nace_r2", "year"]

mpi_sample = bdi_panel.loc[
    bdi_panel["bdi_mpi_complete"].eq(True)
].copy()

if mpi_sample.duplicated(keys).any():
    raise ValueError("Duplicate descriptive-sample keys.")

required_values = [
    "birth_rate",
    "survival_3y",
    "high_growth_share",
    "bdi_mpi_mean",
    "bdi_mpi_penalty",
    "bdi_mpi",
]

if not np.isfinite(
    mpi_sample[required_values].to_numpy()
).all():
    raise ValueError("Missing or non-finite descriptive values.")

if not np.allclose(
    mpi_sample["bdi_mpi"],
    mpi_sample["bdi_mpi_mean"]
    - mpi_sample["bdi_mpi_penalty"],
):
    raise ValueError("MPI decomposition does not match.")

# Контекстные показатели в исходных процентах.
mpi_sample["churn"] = (
    mpi_sample["birth_rate"] + mpi_sample["death_rate"]
)


# %%
# Средние индивидуальных MPI, а не MPI агрегированных компонентов.
# Компоненты в этих таблицах представлены исходными значениями.

def summarize_mpi(data, group_columns):
    return (
        data.groupby(group_columns)
        .agg(
            n_observations=("bdi_mpi", "count"),
            mean_mpi=("bdi_mpi", "mean"),
            median_mpi=("bdi_mpi", "median"),
            std_mpi=("bdi_mpi", "std"),
            mean_level=("bdi_mpi_mean", "mean"),
            mean_penalty=("bdi_mpi_penalty", "mean"),
            mean_birth_rate=("birth_rate", "mean"),
            mean_survival_3y=("survival_3y", "mean"),
            mean_high_growth_share=("high_growth_share", "mean"),
            mean_death_rate=("death_rate", "mean"),
            n_death_rate=("death_rate", "count"),
            mean_churn=("churn", "mean"),
            n_churn=("churn", "count"),
        )
        .reset_index()
    )


summary_year = summarize_mpi(mpi_sample, ["year"])

summary_country = summarize_mpi(
    mpi_sample, ["geo"]
).sort_values("mean_mpi", ascending=False)

summary_nace = summarize_mpi(
    mpi_sample, ["nace_r2"]
).sort_values("mean_mpi", ascending=False)

summary_country_year = summarize_mpi(
    mpi_sample, ["geo", "year"]
)

industry_counts = (
    mpi_sample.groupby(["geo", "year"])["nace_r2"]
    .nunique()
    .rename("n_industries")
    .reset_index()
)

summary_country_year = summary_country_year.merge(
    industry_counts,
    on=["geo", "year"],
    validate="one_to_one",
)


# %%
# Корреляции исходных компонентов на MPI-выборке.

component_spearman = mpi_sample[
    [
        "birth_rate",
        "survival_3y",
        "high_growth_share",
    ]
].corr(method="spearman")


# %%
# Постоянный состав пар для анализа временной динамики.
# Пара сохраняется только при наличии MPI во всех годах периода.

years = sorted(bdi_panel["year"].unique())

pair_year_counts = mpi_sample.groupby(
    ["geo", "nace_r2"]
)["year"].nunique()

balanced_pairs = pair_year_counts.loc[
    pair_year_counts == len(years)
].index

sample_pair_keys = pd.MultiIndex.from_frame(
    mpi_sample[["geo", "nace_r2"]]
)

balanced_sample = mpi_sample.loc[
    sample_pair_keys.isin(balanced_pairs)
].copy()

if balanced_sample.empty:
    raise ValueError("Empty balanced descriptive sample.")

balanced_summary_year = summarize_mpi(
    balanced_sample, ["year"]
).sort_values("year")

balanced_summary_year["change_in_mean_level"] = (
    balanced_summary_year["mean_level"].diff()
)

balanced_summary_year["change_in_mean_penalty"] = (
    balanced_summary_year["mean_penalty"].diff()
)

balanced_summary_year["change_in_mean_mpi"] = (
    balanced_summary_year["mean_mpi"].diff()
)


# %%
# Таблицы быстрого сравнения стран по годам.
# Непостоянное отраслевое покрытие видно в отдельной таблице.

country_year_mpi_table = summary_country_year.pivot(
    index="geo",
    columns="year",
    values="mean_mpi",
)

country_year_industry_counts = summary_country_year.pivot(
    index="geo",
    columns="year",
    values="n_industries",
)

# Среднее годовых средних, не взвешенное по числу наблюдений.
country_year_mpi_table["mean_of_year_means"] = (
    country_year_mpi_table.mean(axis=1)
)

country_year_mpi_table = country_year_mpi_table.sort_values(
    "mean_of_year_means",
    ascending=False,
)

# Выживаемость на той же аналитической выборке.
survival_country_year_table = summary_country_year.pivot(
    index="geo",
    columns="year",
    values="mean_survival_3y",
)

survival_country_year_table["mean_of_year_means"] = (
    survival_country_year_table.mean(axis=1)
)


# %%
# Сохранение

tables = {
    "bdi_mpi_summary_year": (summary_year, False),
    "bdi_mpi_summary_country": (summary_country, False),
    "bdi_mpi_summary_nace": (summary_nace, False),
    "bdi_mpi_summary_country_year": (
        summary_country_year, False
    ),
    "bdi_mpi_component_spearman": (component_spearman, True),
    "bdi_mpi_balanced_summary_year": (
        balanced_summary_year, False
    ),
    "bdi_mpi_country_year_table": (
        country_year_mpi_table, True
    ),
    "bdi_mpi_country_year_industry_counts": (
        country_year_industry_counts, True
    ),
    "bdi_mpi_survival_country_year_table": (
        survival_country_year_table, True
    ),
}

for filename, (table, save_index) in tables.items():
    table.to_csv(
        descriptive_dir / f"{filename}.csv",
        index=save_index,
    )

balanced_sample[
    keys + ["bdi_mpi_mean", "bdi_mpi_penalty", "bdi_mpi"]
].to_csv(
    descriptive_dir / "bdi_mpi_balanced_observations.csv",
    index=False,
)


# %%
print("MPI descriptive observations:", len(mpi_sample))
print("Balanced pairs:", len(balanced_pairs))
print("Balanced observations:", len(balanced_sample))

print("\nMPI SUMMARY BY COUNTRY")
print(
    summary_country[
        [
            "geo",
            "n_observations",
            "mean_mpi",
            "mean_level",
            "mean_penalty",
        ]
    ].round(4).to_string(index=False)
)

print("\nMPI SUMMARY BY INDUSTRY")
print(
    summary_nace[
        [
            "nace_r2",
            "n_observations",
            "mean_mpi",
            "mean_level",
            "mean_penalty",
        ]
    ].round(4).to_string(index=False)
)

print("\nMPI BALANCED YEAR SUMMARY")
print(
    balanced_summary_year[
        [
            "year",
            "n_observations",
            "mean_mpi",
            "mean_level",
            "mean_penalty",
            "change_in_mean_level",
            "change_in_mean_penalty",
            "change_in_mean_mpi",
        ]
    ].round(4).to_string(index=False)
)

print("\nMPI COMPONENT SPEARMAN")
print(component_spearman.round(4).to_string())