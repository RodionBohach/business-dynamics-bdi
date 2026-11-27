# %%
# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parents[1]

descriptive_dir = project_root / "outputs/descriptive"
figures_dir = project_root / "outputs/figures"
figures_dir.mkdir(parents=True, exist_ok=True)

year_summary = pd.read_csv(
    descriptive_dir / "bdi_mpi_balanced_summary_year.csv"
).sort_values("year")

country_summary = pd.read_csv(
    descriptive_dir / "bdi_mpi_summary_country.csv"
)

industry_summary = pd.read_csv(
    descriptive_dir / "bdi_mpi_summary_nace.csv"
)

# Общий стиль для всех рисунков.
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

BLUE = "#245A81"
ORANGE = "#C47726"
GRAY = "#737373"


def save_figure(fig, filename):
    """Сохраняет рисунок для Word и в векторном формате."""
    fig.savefig(
        figures_dir / f"{filename}.png",
        dpi=300,
        bbox_inches="tight",
    )
    fig.savefig(
        figures_dir / f"{filename}.pdf",
        bbox_inches="tight",
    )
    plt.close(fig)
    print(f"Saved: {filename}.png and {filename}.pdf")


# %%
# 1. Динамика: одинаковые пары страна–отрасль во всех годах.

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    year_summary["year"],
    year_summary["mean_level"],
    color=ORANGE,
    marker="s",
    linestyle="--",
    label="Mean before penalty",
)

ax.plot(
    year_summary["year"],
    year_summary["mean_mpi"],
    color=BLUE,
    marker="o",
    linewidth=2,
    label="BDI (MPI)",
)

ax.fill_between(
    year_summary["year"].to_numpy(),
    year_summary["mean_mpi"].to_numpy(),
    year_summary["mean_level"].to_numpy(),
    color=GRAY,
    alpha=0.15,
    label="Mean imbalance penalty",
)

ax.axhline(100, color=GRAY, linewidth=1, linestyle=":")
ax.set_xticks(year_summary["year"])
ax.set_xlabel("Year")
ax.set_ylabel("Index points")
ax.set_title("BDI and component mean, 2013–2020")
ax.grid(axis="y", alpha=0.2)
ax.legend(frameon=False, fontsize=9)

fig.text(
    0.12,
    0.02,
    "Balanced panel: 237 country–industry pairs. "
    "Fixed normalization; 100 is the component reference level.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.06, 1, 1))
save_figure(fig, "mpi_01_historical_dynamics")


# %%
# 2. Изменение MPI = изменение среднего − изменение штрафа.

changes = year_summary.loc[
    year_summary["change_in_mean_mpi"].notna()
].copy()

changes["penalty_contribution"] = (
    -changes["change_in_mean_penalty"]
)

if not np.allclose(
    changes["change_in_mean_level"]
    + changes["penalty_contribution"],
    changes["change_in_mean_mpi"],
    atol=1e-8,
):
    raise ValueError("Annual change decomposition does not match.")

positions = np.arange(len(changes))
bar_width = 0.34

fig, ax = plt.subplots(figsize=(9, 5))

ax.bar(
    positions - bar_width / 2,
    changes["change_in_mean_level"],
    width=bar_width,
    color=BLUE,
    label="Change in component mean",
)

ax.bar(
    positions + bar_width / 2,
    changes["penalty_contribution"],
    width=bar_width,
    color=ORANGE,
    label="Contribution from penalty change",
)

ax.plot(
    positions,
    changes["change_in_mean_mpi"],
    color="#222222",
    marker="D",
    linestyle="none",
    markersize=5,
    label="Net change in BDI",
)

ax.axhline(0, color=GRAY, linewidth=1)
ax.set_xticks(positions)
ax.set_xticklabels(changes["year"].astype(int))
ax.set_xlabel("Year")
ax.set_ylabel("Change from previous year, index points")
ax.set_title("Sources of annual BDI change")
ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9)

fig.text(
    0.12,
    0.02,
    "Positive penalty contribution means that the imbalance penalty decreased. "
    "Balanced panel: 237 pairs.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.06, 1, 1))
save_figure(fig, "mpi_02_annual_change_decomposition")


# %%
# 3–4. Сравнение стран и отраслей.
# Точка показывает средний MPI, подпись — число наблюдений.

country_names = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CZ": "Czechia",
    "DE": "Germany",
    "EE": "Estonia",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "HU": "Hungary",
    "IT": "Italy",
    "LV": "Latvia",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
}

industry_names = {
    "B": "Mining and quarrying",
    "C": "Manufacturing",
    "D": "Electricity, gas and steam",
    "E": "Water, sewerage and waste",
    "F": "Construction",
    "G": "Wholesale and retail trade",
    "H": "Transportation and storage",
    "I": "Accommodation and food services",
    "J": "Information and communication",
    "L": "Real estate",
    "M": "Professional, scientific and technical",
    "N": "Administrative and support services",
}


def plot_group_comparison(
    summary,
    group_column,
    names,
    title,
    note,
    filename,
    height,
):
    table = summary.sort_values(
        "mean_mpi", ascending=False
    ).copy()

    labels = [
        f"{code} — {names.get(code, code)}"
        for code in table[group_column]
    ]
    positions = np.arange(len(table))

    fig, ax = plt.subplots(figsize=(10, height))

    ax.scatter(
        table["mean_mpi"],
        positions,
        color=BLUE,
        s=45,
        zorder=3,
    )

    for position, (_, row) in zip(
        positions, table.iterrows()
    ):
        ax.annotate(
            f'{row["mean_mpi"]:.2f}  '
            f'(n={int(row["n_observations"])})',
            (row["mean_mpi"], position),
            xytext=(9, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
        )

    minimum = min(100, table["mean_mpi"].min())
    maximum = max(100, table["mean_mpi"].max())
    span = max(maximum - minimum, 1)

    ax.set_xlim(
        minimum - 0.08 * span,
        maximum + 0.40 * span,
    )

    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.axvline(
        100,
        color=GRAY,
        linestyle=":",
        linewidth=1,
    )
    ax.set_xlabel("Mean BDI (MPI), index points")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    fig.text(
        0.02,
        0.02,
        note,
        fontsize=8,
        color=GRAY,
    )

    fig.tight_layout(rect=(0, 0.07, 1, 1))
    save_figure(fig, filename)


plot_group_comparison(
    summary=country_summary,
    group_column="geo",
    names=country_names,
    title="Mean BDI by country, 2013–2020",
    note=(
        "Unweighted means of available industry–year observations. "
        "Coverage differs for Norway and Romania."
    ),
    filename="mpi_03_country_comparison",
    height=8,
)

plot_group_comparison(
    summary=industry_summary,
    group_column="nace_r2",
    names=industry_names,
    title="Mean BDI by industry, 2013–2020",
    note=(
        "Unweighted means of available country–year observations. "
        "Results use pooled normalization across industries."
    ),
    filename="mpi_04_industry_comparison",
    height=6,
)

print("\nFour figures saved to:", figures_dir)

# %%
# 5. Историческое сравнение survival-горизонтов S1/S2/S3.

horizon_sample = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "mpi_survival_horizon_comparison.csv"
)

keys = ["geo", "nace_r2", "year"]
horizon_columns = ["mpi_s1", "mpi_s2", "mpi_s3"]

required_columns = keys + horizon_columns
missing_columns = set(required_columns) - set(
    horizon_sample.columns
)

if missing_columns:
    raise ValueError(
        f"Missing columns: {sorted(missing_columns)}. "
        f"Available columns: {horizon_sample.columns.tolist()}"
    )

horizon_sample = horizon_sample.loc[
    horizon_sample["year"].between(2013, 2020)
].copy()

if horizon_sample.duplicated(keys).any():
    raise ValueError("Duplicate country–industry–year keys.")

horizon_sample = horizon_sample.dropna(
    subset=horizon_columns
).copy()

if not np.isfinite(
    horizon_sample[horizon_columns].to_numpy()
).all():
    raise ValueError("Non-finite MPI values.")

# Для динамики оставляем только пары со всеми восемью годами.
expected_years = list(range(2013, 2021))

pair_year_counts = (
    horizon_sample.groupby(["geo", "nace_r2"])["year"]
    .nunique()
)

balanced_pairs = (
    pair_year_counts.loc[
        pair_year_counts == len(expected_years)
    ]
    .rename("n_years")
    .reset_index()[["geo", "nace_r2"]]
)

if balanced_pairs.empty:
    raise ValueError("No complete eight-year pairs.")

balanced_horizons = horizon_sample.merge(
    balanced_pairs,
    on=["geo", "nace_r2"],
    how="inner",
    validate="many_to_one",
)

horizon_year_summary = (
    balanced_horizons.groupby("year")[horizon_columns]
    .mean()
    .reindex(expected_years)
)

horizon_year_summary.to_csv(
    descriptive_dir
    / "mpi_horizon_balanced_year_summary.csv"
)

balanced_horizons[
    keys + horizon_columns
].to_csv(
    descriptive_dir
    / "mpi_horizon_balanced_plot_sample.csv",
    index=False,
)

horizon_styles = {
    "mpi_s1": {
        "label": "S1: one-year survival",
        "color": BLUE,
        "marker": "o",
        "linestyle": "-",
    },
    "mpi_s2": {
        "label": "S2: two-year survival",
        "color": ORANGE,
        "marker": "s",
        "linestyle": "--",
    },
    "mpi_s3": {
        "label": "S3: three-year survival",
        "color": "#327A58",
        "marker": "^",
        "linestyle": "-.",
    },
}

fig, ax = plt.subplots(figsize=(9, 5))

for column, style in horizon_styles.items():
    ax.plot(
        horizon_year_summary.index,
        horizon_year_summary[column],
        linewidth=2,
        **style,
    )

ax.axhline(
    100,
    color=GRAY,
    linestyle=":",
    linewidth=1,
)

ax.set_xticks(expected_years)
ax.set_xlabel("Year")
ax.set_ylabel("Mean BDI (MPI), index points")
ax.set_title("BDI under alternative survival horizons")
ax.grid(axis="y", alpha=0.2)
ax.legend(frameon=False, fontsize=9)

fig.text(
    0.12,
    0.02,
    f"Balanced panel: {len(balanced_pairs)} pairs. "
    "Fixed historical normalization for each variant.\n"
    "Only the survival horizon changes; high-growth remains "
    "a three-year measure.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.10, 1, 1))
save_figure(fig, "mpi_05_survival_horizon_dynamics")


# %%
# 6. Сравнение рангов на общей исторической выборке.
# Ранги считаются среди всех country–industry–year наблюдений,
# а не отдельно внутри каждого года.

rank_columns = {}

for column in horizon_columns:
    rank_name = f"plot_rank_{column}"

    horizon_sample[rank_name] = (
        horizon_sample[column].rank(
            ascending=False,
            method="average",
        )
    )

    rank_columns[column] = rank_name

comparisons = [
    ("mpi_s1", "mpi_s3", "S1 versus S3"),
    ("mpi_s2", "mpi_s3", "S2 versus S3"),
    ("mpi_s1", "mpi_s2", "S1 versus S2"),
]

fig, axes = plt.subplots(
    1,
    3,
    figsize=(13, 4.8),
    sharex=True,
    sharey=True,
)

n_observations = len(horizon_sample)

for ax, (first, second, title) in zip(
    axes, comparisons
):
    first_rank = horizon_sample[rank_columns[first]]
    second_rank = horizon_sample[rank_columns[second]]

    rho = horizon_sample[[first, second]].corr(
        method="spearman"
    ).iloc[0, 1]

    median_shift = (
        first_rank - second_rank
    ).abs().median()

    ax.scatter(
        first_rank,
        second_rank,
        s=9,
        alpha=0.25,
        color=BLUE,
        edgecolors="none",
        rasterized=True,
    )

    ax.plot(
        [1, n_observations],
        [1, n_observations],
        color=GRAY,
        linestyle="--",
        linewidth=1,
    )

    ax.set_title(title)
    ax.set_xlabel(f"Rank: {first.replace('mpi_', '').upper()}")
    ax.set_xlim(0, n_observations + 1)
    ax.set_ylim(0, n_observations + 1)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)

    ax.text(
        0.04,
        0.96,
        f"Spearman rho = {rho:.3f}\n"
        f"Median absolute shift = {median_shift:.1f}",
        transform=ax.transAxes,
        va="top",
        fontsize=9,
        bbox={
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.9,
        },
    )

axes[0].set_ylabel("Rank of second variant")

fig.suptitle(
    "Ranking sensitivity to the survival horizon",
    fontsize=13,
)

fig.text(
    0.05,
    0.02,
    f"Common historical sample: {n_observations:,} observations. "
    "Rank 1 is highest; the diagonal indicates identical ranks.\n"
    "Each point represents one country–industry–year observation.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.10, 1, 0.94))
save_figure(fig, "mpi_06_survival_horizon_ranks")

print(
    "\nHistorical horizon comparison:",
    len(horizon_sample),
    "observations",
)
print(
    "Balanced horizon panel:",
    len(balanced_pairs),
    "pairs and",
    len(balanced_horizons),
    "observations",
)

# %%
# 7. Примеры действия штрафа MPI.

panel = pd.read_csv(
    project_root / "data/final/BDI_panel.csv"
)

mpi_components = [
    "birth_rate",
    "survival_3y",
    "high_growth_share",
]

analytical_columns = [
    f"mpi_analytical_{component}"
    for component in mpi_components
]

parameters = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "bdi_mpi_normalization_parameters.csv"
).set_index("component")

# Используем только наблюдения с рассчитанным MPI.
penalty_sample = panel.dropna(
    subset=analytical_columns + [
        "bdi_mpi",
        "bdi_mpi_mean",
        "bdi_mpi_penalty",
    ]
).copy()

reference_means = parameters.loc[
    mpi_components, "mean_after_winsorization"
]

reference_stds = parameters.loc[
    mpi_components, "std_after_winsorization_ddof0"
]

analytical_values = penalty_sample[
    analytical_columns
].copy()

analytical_values.columns = mpi_components

normalized_values = (
    100
    + 10
    * (analytical_values - reference_means)
    / reference_stds
)

# Проверяем, что восстановили именно использованную шкалу.
reconstructed_mean = normalized_values.mean(axis=1)
reconstructed_variance = normalized_values.var(
    axis=1,
    ddof=0,
)
reconstructed_penalty = (
    reconstructed_variance / reconstructed_mean
)

if not np.allclose(
    reconstructed_mean,
    penalty_sample["bdi_mpi_mean"],
    atol=1e-8,
):
    raise ValueError("MPI component means do not match.")

if not np.allclose(
    reconstructed_penalty,
    penalty_sample["bdi_mpi_penalty"],
    atol=1e-8,
):
    raise ValueError("MPI penalties do not match.")

# Выбор примеров.
largest_penalty_index = (
    penalty_sample["bdi_mpi_penalty"].idxmax()
)

remaining_sample = penalty_sample.drop(
    index=largest_penalty_index
)

median_penalty = penalty_sample[
    "bdi_mpi_penalty"
].median()

typical_penalty_index = (
    remaining_sample["bdi_mpi_penalty"]
    .sub(median_penalty)
    .abs()
    .idxmin()
)

high_level_threshold = penalty_sample[
    "bdi_mpi_mean"
].quantile(0.90)

high_level_sample = penalty_sample.loc[
    penalty_sample["bdi_mpi_mean"]
    >= high_level_threshold
].drop(
    index=[
        largest_penalty_index,
        typical_penalty_index,
    ],
    errors="ignore",
)

balanced_high_index = (
    high_level_sample["bdi_mpi_penalty"].idxmin()
)

case_indices = [
    largest_penalty_index,
    typical_penalty_index,
    balanced_high_index,
]

case_titles = [
    "Largest penalty",
    "Penalty closest to median",
    "Smallest penalty within top 10% by mean",
]

component_labels = [
    "Enterprise birth rate",
    "Three-year survival",
    "High-growth share",
]

case_normalized = normalized_values.loc[
    case_indices
]

# Единая шкала во всех трёх панелях.
minimum_value = min(
    100,
    case_normalized.min().min(),
)
maximum_value = max(
    100,
    case_normalized.max().max(),
)

scale_span = max(
    maximum_value - minimum_value,
    10,
)

x_minimum = minimum_value - 0.15 * scale_span
x_maximum = maximum_value + 0.20 * scale_span

fig, axes = plt.subplots(
    1,
    3,
    figsize=(14, 5),
    sharex=True,
    sharey=True,
)

for ax, case_index, case_title in zip(
    axes,
    case_indices,
    case_titles,
):
    row = penalty_sample.loc[case_index]
    values = normalized_values.loc[
        case_index
    ].to_numpy()

    positions = np.arange(len(mpi_components))

    # Длина столбца — отклонение от референсного уровня 100.
    ax.barh(
        positions,
        values - 100,
        left=100,
        height=0.5,
        color=BLUE,
        alpha=0.85,
    )

    ax.axvline(
        100,
        color=GRAY,
        linestyle=":",
        linewidth=1,
    )

    for position, value in zip(positions, values):
        offset = 5 if value >= 100 else -5
        alignment = "left" if value >= 100 else "right"

        ax.annotate(
            f"{value:.1f}",
            (value, position),
            xytext=(offset, 0),
            textcoords="offset points",
            va="center",
            ha=alignment,
            fontsize=9,
        )

    case_label = (
        f'{row["geo"]} / {row["nace_r2"]} / '
        f'{int(row["year"])}'
    )

    ax.set_title(
        f"{case_title}\n{case_label}",
        fontsize=10,
    )

    ax.set_yticks(positions)
    ax.set_yticklabels(component_labels)
    ax.set_xlim(x_minimum, x_maximum)
    ax.set_xlabel("Normalized component score")
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)

    ax.text(
        0.02,
        -0.45,
        f'Mean: {row["bdi_mpi_mean"]:.2f}\n'
        f'Penalty: {row["bdi_mpi_penalty"]:.2f}\n'
        f'BDI: {row["bdi_mpi"]:.2f}',
        transform=ax.transAxes,
        fontsize=10,
        va="top",
    )

axes[0].invert_yaxis()

fig.suptitle(
    "How the MPI imbalance penalty works",
    fontsize=14,
)

fig.text(
    0.03,
    0.02,
    "BDI = component mean − imbalance penalty. "
    "Bars show deviations from each component's reference level of 100.\n"
    "Scores use winsorized values and fixed historical normalization; "
    "they are not raw percentages.",
    fontsize=8,
    color=GRAY,
)

fig.subplots_adjust(
    left=0.16,
    right=0.98,
    bottom=0.40,
    top=0.78,
    wspace=0.18,
)
save_figure(fig, "mpi_07_penalty_examples")

# Сохраняем выбранные примеры вместе с исходными значениями.
penalty_cases = penalty_sample.loc[
    case_indices,
    keys
    + mpi_components
    + analytical_columns
    + [
        "bdi_mpi_mean",
        "bdi_mpi_penalty",
        "bdi_mpi",
    ],
].copy()

penalty_cases.insert(
    0,
    "selection_rule",
    case_titles,
)

for component in mpi_components:
    penalty_cases[f"normalized_{component}"] = (
        normalized_values.loc[
            case_indices, component
        ].to_numpy()
    )

penalty_cases.to_csv(
    descriptive_dir / "mpi_penalty_plot_examples.csv",
    index=False,
)

print("\nMPI PENALTY EXAMPLES")
print(
    penalty_cases[
        [
            "selection_rule",
            "geo",
            "nace_r2",
            "year",
            "bdi_mpi_mean",
            "bdi_mpi_penalty",
            "bdi_mpi",
        ]
    ].round(3).to_string(index=False)
)


# %%
# 8. Коэффициенты FE-регрессии.
# Изменение MPI при увеличении X на одно within-SD.
# Используем готовые оценки и страновые доверительные интервалы.

scaled_coefficients = pd.read_csv(
    project_root
    / "outputs/models"
    / "fixed_effects_mpi_scaled_coefficients.csv",
    index_col=0,
)

predictor_order = [
    "investment_intensity",
    "labour_share",
    "log_labour_productivity",
    "employment_growth",
]

predictor_labels = {
    "investment_intensity": "Investment intensity",
    "labour_share": "Labour share",
    "log_labour_productivity": "Log labour productivity",
    "employment_growth": "Employment growth",
}

coefficient_table = scaled_coefficients.loc[
    predictor_order,
    [
        "scaled_coefficient",
        "scaled_ci_lower",
        "scaled_ci_upper",
    ],
].copy()

if not np.isfinite(
    coefficient_table.to_numpy()
).all():
    raise ValueError("Non-finite coefficient or interval.")

lower_errors = (
    coefficient_table["scaled_coefficient"]
    - coefficient_table["scaled_ci_lower"]
)

upper_errors = (
    coefficient_table["scaled_ci_upper"]
    - coefficient_table["scaled_coefficient"]
)

if (lower_errors < 0).any() or (upper_errors < 0).any():
    raise ValueError("Invalid confidence intervals.")

positions = np.arange(len(coefficient_table))

fig, ax = plt.subplots(figsize=(9, 5))

ax.errorbar(
    coefficient_table["scaled_coefficient"],
    positions,
    xerr=np.vstack([
        lower_errors.to_numpy(),
        upper_errors.to_numpy(),
    ]),
    fmt="o",
    color=BLUE,
    ecolor=BLUE,
    capsize=5,
    markersize=6,
    linewidth=1.7,
)

ax.axvline(
    0,
    color=GRAY,
    linestyle="--",
    linewidth=1,
)

ax.set_yticks(positions)
ax.set_yticklabels([
    predictor_labels[variable]
    for variable in predictor_order
])
ax.invert_yaxis()

ax.set_xlabel(
    "BDI change per one within-standard-deviation increase in X"
)
ax.set_title(
    "Fixed-effects estimates with 95% confidence intervals"
)
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

fig.text(
    0.03,
    0.02,
    "Country–industry and year fixed effects; "
    "country-clustered, t-based confidence intervals.\n"
    "N = 1,917; 20 country clusters. "
    "Estimates describe conditional associations, not causal effects.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.12, 1, 1))
save_figure(fig, "mpi_08_fe_scaled_coefficients")

for filename in [
    "modern_mpi_dynamics_balanced.csv",
    "modern_mpi_2024_horizon_comparison.csv",
]:
    table = pd.read_csv(
        project_root / "outputs/diagnostics" / filename
    )
    print(f"\n{filename}")
    print(table.columns.tolist())
    print(table.head(2).to_string(index=False))

    # %%
# 9. Современная динамика S1 и S2.
# У каждого горизонта своя постоянная выборка пар.

modern_balanced = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "modern_mpi_dynamics_balanced.csv"
)

modern_keys = [
    "geo",
    "nace_r2",
    "year",
    "survival_horizon",
]

if modern_balanced.duplicated(modern_keys).any():
    raise ValueError("Duplicate modern horizon keys.")

modern_periods = {
    1: [2022, 2023, 2024],
    2: [2023, 2024],
}

modern_colors = {
    1: BLUE,
    2: ORANGE,
    3: "#327A58",
}

modern_plot_summaries = []

for horizon, years in modern_periods.items():
    subset = modern_balanced.loc[
        modern_balanced["survival_horizon"].eq(horizon)
        & modern_balanced["year"].isin(years)
    ].copy()

    if subset.empty:
        raise ValueError(f"No observations for S{horizon}.")

    if subset[
        ["bdi_mpi", "mean_level", "penalty"]
    ].isna().any().any():
        raise ValueError(f"Missing model values for S{horizon}.")

    pair_counts = subset.groupby(
        ["geo", "nace_r2"]
    )["year"].nunique()

    if not pair_counts.eq(len(years)).all():
        raise ValueError(f"S{horizon} panel is not balanced.")

    summary = (
        subset.groupby("year")
        .agg(
            mean_mpi=("bdi_mpi", "mean"),
            mean_level=("mean_level", "mean"),
            mean_penalty=("penalty", "mean"),
            n_observations=("bdi_mpi", "count"),
        )
        .reindex(years)
        .reset_index()
    )

    summary["survival_horizon"] = horizon
    modern_plot_summaries.append(summary)

modern_dynamics_plot_summary = pd.concat(
    modern_plot_summaries,
    ignore_index=True,
)

modern_dynamics_plot_summary.to_csv(
    descriptive_dir / "modern_mpi_dynamics_plot_summary.csv",
    index=False,
)

fig, axes = plt.subplots(
    1,
    2,
    figsize=(11, 5),
    sharey=True,
)

for ax, horizon in zip(axes, modern_periods):
    summary = modern_dynamics_plot_summary.loc[
        modern_dynamics_plot_summary[
            "survival_horizon"
        ].eq(horizon)
    ]

    n_pairs = int(summary["n_observations"].iloc[0])

    ax.plot(
        summary["year"],
        summary["mean_mpi"],
        color=modern_colors[horizon],
        marker="o",
        linewidth=2,
        label="BDI (MPI)",
    )

    ax.plot(
        summary["year"],
        summary["mean_level"],
        color=GRAY,
        marker="s",
        linestyle="--",
        label="Mean before penalty",
    )

    ax.fill_between(
        summary["year"].to_numpy(),
        summary["mean_mpi"].to_numpy(),
        summary["mean_level"].to_numpy(),
        color=GRAY,
        alpha=0.12,
    )

    ax.axhline(
        100,
        color=GRAY,
        linestyle=":",
        linewidth=1,
    )

    ax.set_xticks(modern_periods[horizon])
    ax.set_xlabel("Year")
    ax.set_title(
        f"S{horizon}: {horizon}-year survival\n"
        f"Balanced panel: {n_pairs} pairs"
    )
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, fontsize=9)

axes[0].set_ylabel("Mean index points")

fig.suptitle(
    "Modern BDI dynamics under alternative survival horizons",
    fontsize=13,
)

fig.text(
    0.04,
    0.02,
    "Fixed 2024 reference parameters. Historical years are assessed "
    "retrospectively against that reference.\n"
    "Each panel uses a constant sample; samples differ between panels. "
    "High-growth remains a three-year measure.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.13, 1, 0.91))
save_figure(fig, "mpi_09_modern_horizon_dynamics")


# %%
# 10. Сравнение S1/S2/S3 по странам за 2024 год.
# Для всех трёх вариантов используем одинаковые наблюдения.

modern_snapshot = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "modern_mpi_2024_horizon_comparison.csv"
)

modern_snapshot = modern_snapshot.loc[
    modern_snapshot["year"].eq(2024)
].dropna(
    subset=["mpi_s1", "mpi_s2", "mpi_s3"]
).copy()

if modern_snapshot.duplicated(
    ["geo", "nace_r2", "year"]
).any():
    raise ValueError("Duplicate 2024 snapshot keys.")

modern_country_comparison = (
    modern_snapshot.groupby("geo")
    .agg(
        n_industries=("nace_r2", "nunique"),
        mpi_s1=("mpi_s1", "mean"),
        mpi_s2=("mpi_s2", "mean"),
        mpi_s3=("mpi_s3", "mean"),
    )
    .sort_values("mpi_s3", ascending=False)
)

modern_country_comparison.to_csv(
    descriptive_dir
    / "modern_mpi_2024_country_horizon_plot_data.csv",
    index=True,
)

fig, ax = plt.subplots(figsize=(10, 9))

positions = np.arange(len(modern_country_comparison))

# Отрезок показывает диапазон трёх средних оценок страны.
ax.hlines(
    positions,
    modern_country_comparison[
        ["mpi_s1", "mpi_s2", "mpi_s3"]
    ].min(axis=1),
    modern_country_comparison[
        ["mpi_s1", "mpi_s2", "mpi_s3"]
    ].max(axis=1),
    color="#BBBBBB",
    linewidth=2,
    zorder=1,
)

for horizon, marker in [(1, "o"), (2, "s"), (3, "^")]:
    ax.scatter(
        modern_country_comparison[f"mpi_s{horizon}"],
        positions,
        color=modern_colors[horizon],
        marker=marker,
        s=45,
        label=f"S{horizon}",
        zorder=3,
    )

labels = [
    f"{geo} — {country_names.get(geo, geo)} "
    f"(n={int(row['n_industries'])})"
    for geo, row in modern_country_comparison.iterrows()
]

ax.set_yticks(positions)
ax.set_yticklabels(labels)
ax.invert_yaxis()

ax.axvline(
    100,
    color=GRAY,
    linestyle=":",
    linewidth=1,
)

ax.set_xlabel("Mean BDI (MPI), index points")
ax.set_title(
    "Country comparison by survival horizon, 2024"
)
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)
ax.legend(
    frameon=False,
    title="Survival horizon",
    loc="best",
)

fig.text(
    0.03,
    0.02,
    f"Common sample: {len(modern_snapshot)} country–industry "
    "observations; unweighted industry means.\n"
    "Countries are ordered by S3. Norway and Hungary have fewer "
    "included industries.\n"
    "Each survival component uses its own fixed 2024 normalization. "
    "Scores are not survival probabilities.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.12, 1, 1))
save_figure(fig, "mpi_10_modern_country_horizons")

print("\nMODERN DYNAMICS PLOT SUMMARY")
print(
    modern_dynamics_plot_summary.round(4).to_string(
        index=False
    )
)

print(
    "\n2024 common horizon sample:",
    len(modern_snapshot),
)

modern_available = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "modern_mpi_dynamics_available.csv"
)

print(modern_available.columns.tolist())
print(modern_available.head(2).to_string(index=False))

# %%
# 11. Разложение изменения современного MPI: 2023 → 2024.

modern_available = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "modern_mpi_dynamics_available.csv"
)

modern_balanced = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "modern_mpi_dynamics_balanced.csv"
)

join_keys = ["geo", "nace_r2", "year"]

if modern_available.duplicated(join_keys).any():
    raise ValueError("Duplicate modern component keys.")

component_change_rows = []
index_change_rows = []

for horizon in [1, 2]:
    components = [
        "birth_rate",
        f"survival_{horizon}y",
        "high_growth_share",
    ]

    normalized_columns = [
        f"mpi_normalized_{component}"
        for component in components
    ]

    analytical_columns = [
        f"mpi_analytical_{component}"
        for component in components
    ]

    balanced_subset = modern_balanced.loc[
        modern_balanced["survival_horizon"].eq(horizon)
        & modern_balanced["year"].isin([2023, 2024])
    ].copy()

    if balanced_subset.duplicated(join_keys).any():
        raise ValueError(f"Duplicate balanced keys for S{horizon}.")

    pair_counts = balanced_subset.groupby(
        ["geo", "nace_r2"]
    )["year"].nunique()

    if balanced_subset.empty or not pair_counts.eq(2).all():
        raise ValueError(f"Incomplete paired sample for S{horizon}.")

    comparison = balanced_subset.merge(
        modern_available[
            join_keys
            + components
            + analytical_columns
            + normalized_columns
        ],
        on=join_keys,
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if not comparison["_merge"].eq("both").all():
        raise ValueError(f"Unmatched component rows for S{horizon}.")

    value_columns = (
        components
        + analytical_columns
        + normalized_columns
        + ["bdi_mpi", "mean_level", "penalty"]
    )

    if not np.isfinite(
        comparison[value_columns].to_numpy()
    ).all():
        raise ValueError(f"Missing or invalid values for S{horizon}.")

    reconstructed_mean = comparison[
        normalized_columns
    ].mean(axis=1)

    if not np.allclose(
        reconstructed_mean,
        comparison["mean_level"],
        atol=1e-8,
    ):
        raise ValueError(f"Component mean mismatch for S{horizon}.")

    if not np.allclose(
        comparison["mean_level"] - comparison["penalty"],
        comparison["bdi_mpi"],
        atol=1e-8,
    ):
        raise ValueError(f"MPI identity mismatch for S{horizon}.")

    year_means = comparison.groupby("year")[
        value_columns
    ].mean()

    contributions = []

    for component in components:
        normalized_column = f"mpi_normalized_{component}"
        analytical_column = f"mpi_analytical_{component}"

        normalized_change = (
            year_means.loc[2024, normalized_column]
            - year_means.loc[2023, normalized_column]
        )

        # Каждый компонент входит в среднее с весом 1/3.
        contribution = normalized_change / 3
        contributions.append(contribution)

        component_change_rows.append({
            "survival_horizon": horizon,
            "n_pairs": len(pair_counts),
            "component": component,
            "raw_mean_2023": year_means.loc[2023, component],
            "raw_mean_2024": year_means.loc[2024, component],
            "raw_change_pp": (
                year_means.loc[2024, component]
                - year_means.loc[2023, component]
            ),
            "analytical_change_pp": (
                year_means.loc[2024, analytical_column]
                - year_means.loc[2023, analytical_column]
            ),
            "normalized_change": normalized_change,
            "contribution_to_mean_change": contribution,
        })

    mean_change = (
        year_means.loc[2024, "mean_level"]
        - year_means.loc[2023, "mean_level"]
    )

    penalty_contribution = -(
        year_means.loc[2024, "penalty"]
        - year_means.loc[2023, "penalty"]
    )

    mpi_change = (
        year_means.loc[2024, "bdi_mpi"]
        - year_means.loc[2023, "bdi_mpi"]
    )

    if not np.isclose(
        sum(contributions),
        mean_change,
        atol=1e-8,
    ):
        raise ValueError("Component contributions do not sum correctly.")

    if not np.isclose(
        sum(contributions) + penalty_contribution,
        mpi_change,
        atol=1e-8,
    ):
        raise ValueError("MPI change decomposition does not match.")

    index_change_rows.append({
        "survival_horizon": horizon,
        "n_pairs": len(pair_counts),
        "mean_change": mean_change,
        "penalty_contribution": penalty_contribution,
        "mpi_change": mpi_change,
    })

component_changes = pd.DataFrame(component_change_rows)
index_changes = pd.DataFrame(index_change_rows)

component_changes.to_csv(
    descriptive_dir
    / "modern_mpi_2023_2024_component_changes.csv",
    index=False,
)

index_changes.to_csv(
    descriptive_dir
    / "modern_mpi_2023_2024_change_decomposition.csv",
    index=False,
)

print("\nCOMPONENT CHANGES: 2023 → 2024")
print(
    component_changes.round(4).to_string(index=False)
)

print("\nMPI CHANGE DECOMPOSITION: 2023 → 2024")
print(
    index_changes.round(4).to_string(index=False)
)

# %%
# Пять воспроизводимо случайных примеров: 2024, S3.

case_source = pd.read_csv(
    project_root
    / "outputs/diagnostics"
    / "modern_mpi_2024_horizon_comparison.csv"
)

case_source = (
    case_source.loc[case_source["year"].eq(2024)]
    .dropna(subset=["mpi_s1", "mpi_s2", "mpi_s3"])
    .sort_values(["geo", "nace_r2"])
    .copy()
)

if case_source.duplicated(["geo", "nace_r2", "year"]).any():
    raise ValueError("Duplicate case-study keys.")

# Ранг считается на всей общей выборке до выбора пяти примеров.
case_source["rank_s3_common"] = case_source["mpi_s3"].rank(
    ascending=False,
    method="average",
)

case_source["churn"] = (
    case_source["birth_rate"] + case_source["death_rate"]
)

case_source["birth_death_gap_pp"] = (
    case_source["birth_rate"] - case_source["death_rate"]
)

case_source["comparison_n"] = len(case_source)

random_cases = (
    case_source.sample(n=5, random_state=42)
    .sort_values("mpi_s3", ascending=False)
)

case_columns = [
    "geo",
    "nace_r2",
    "year",
    "birth_rate",
    "death_rate",
    "churn",
    "birth_death_gap_pp",
    "survival_3y",
    "high_growth_share",
    "mpi_normalized_birth_rate",
    "mpi_normalized_survival_3y",
    "mpi_normalized_high_growth_share",
    "mpi_s3_mean",
    "mpi_s3_penalty",
    "mpi_s3",
    "rank_s3_common",
    "comparison_n",
]

random_cases = random_cases[case_columns].copy()

random_cases.to_csv(
    descriptive_dir / "modern_mpi_2024_five_random_cases.csv",
    index=False,
)

print("\nFIVE RANDOM COUNTRY–INDUSTRY CASES: 2024, S3")
print(random_cases.round(3).to_string(index=False))

# %%
# 12. Связь X с MPI после удаления фиксированных эффектов.

import statsmodels.formula.api as smf

association_sample = pd.read_csv(
    project_root / "data/final/baseline_model_sample.csv"
)

association_predictors = [
    "investment_intensity",
    "labour_share",
    "log_labour_productivity",
    "employment_growth",
]

association_keys = ["geo", "nace_r2", "year"]

required_values = ["bdi_mpi"] + association_predictors

if association_sample.duplicated(association_keys).any():
    raise ValueError("Duplicate model-sample keys.")

if not np.isfinite(
    association_sample[required_values].to_numpy()
).all():
    raise ValueError("Missing or non-finite model values.")

association_sample["panel_id"] = (
    association_sample["geo"]
    + "_"
    + association_sample["nace_r2"]
)

# Для Y и каждого X используем одинаковые фиксированные эффекты.
# Остатки — отклонения, не объясняемые этими эффектами.
residualized = association_sample[association_keys].copy()

for variable in required_values:
    projection = smf.ols(
        f"{variable} ~ C(panel_id) + C(year)",
        data=association_sample,
        missing="raise",
    ).fit()

    residualized[variable] = projection.resid

diagnostics_dir = project_root / "outputs/diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)

residualized.to_csv(
    diagnostics_dir / "mpi_x_fe_residualized_plot_data.csv",
    index=False,
)

association_labels = {
    "investment_intensity": "Investment intensity",
    "labour_share": "Labour share",
    "log_labour_productivity": "Log labour productivity",
    "employment_growth": "Employment growth",
}

association_summary_rows = []

fig, axes = plt.subplots(
    2,
    2,
    figsize=(11, 8),
    sharey=True,
)

for ax, predictor in zip(
    axes.flat,
    association_predictors,
):
    x_values = residualized[predictor].to_numpy()
    y_values = residualized["bdi_mpi"].to_numpy()

    if np.std(x_values) <= 0 or np.std(y_values) <= 0:
        raise ValueError("No residual variation.")

    pearson_r = residualized[
        [predictor, "bdi_mpi"]
    ].corr(method="pearson").iloc[0, 1]

    # Линия простой регрессии очищенного Y на один очищенный X.
    slope, intercept = np.polyfit(
        x_values,
        y_values,
        deg=1,
    )

    line_x = np.array([
        x_values.min(),
        x_values.max(),
    ])

    ax.scatter(
        x_values,
        y_values,
        s=12,
        alpha=0.25,
        color=BLUE,
        edgecolors="none",
        rasterized=True,
    )

    ax.plot(
        line_x,
        intercept + slope * line_x,
        color=ORANGE,
        linewidth=2,
    )

    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.8,
        linestyle=":",
    )

    ax.axvline(
        0,
        color=GRAY,
        linewidth=0.8,
        linestyle=":",
    )

    ax.set_title(association_labels[predictor])
    ax.set_xlabel("X after removing fixed effects")
    ax.set_ylabel("BDI residual, index points")
    ax.grid(alpha=0.15)
    ax.set_axisbelow(True)

    ax.text(
        0.04,
        0.95,
        f"Pearson r = {pearson_r:.3f}",
        transform=ax.transAxes,
        va="top",
        fontsize=10,
        bbox={
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.9,
        },
    )

    association_summary_rows.append({
        "predictor": predictor,
        "pearson_r_after_fe": pearson_r,
        "bivariate_slope_after_fe": slope,
        "n_observations": len(residualized),
    })

fig.suptitle(
    "Associations between X and BDI after removing fixed effects",
    fontsize=13,
)

fig.text(
    0.04,
    0.02,
    "Country–industry and year effects removed from both axes. "
    f"N = {len(residualized):,}.\n"
    "Lines show bivariate linear associations, without controlling "
    "for the other predictors. X-axis scales differ.\n"
    "No causal interpretation or statistical significance "
    "is implied by these plots.",
    fontsize=8,
    color=GRAY,
)

fig.tight_layout(rect=(0, 0.13, 1, 0.94))

save_figure(
    fig,
    "mpi_11_x_associations_after_fixed_effects",
)

association_summary = pd.DataFrame(
    association_summary_rows
)

association_summary.to_csv(
    descriptive_dir / "mpi_x_associations_after_fe.csv",
    index=False,
)

print("\nX–MPI ASSOCIATIONS AFTER FIXED EFFECTS")
print(
    association_summary.round(4).to_string(index=False)
)