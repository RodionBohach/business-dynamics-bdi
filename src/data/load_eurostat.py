# %%
import pandas as pd

# %%
def load_eurostat_data(path):
    df = pd.read_csv(path, sep="\t", compression="gzip", dtype=str, keep_default_na=False)
    df_clean = df.copy()
    df_clean.columns = df_clean.columns.str.strip()
    first_column_name = df_clean.columns[0]
    dimension_names = first_column_name.split("\\")[0].split(",")
    dimensions = df_clean.iloc[:, 0].str.split(",", expand=True)
    dimensions.columns = dimension_names
    df_wide = pd.concat([dimensions, df_clean.iloc[:, 1:]], axis=1)
    df_long = df_wide.melt(
        id_vars=dimension_names,
        var_name="year",
        value_name="value_raw",
    )  
    value_parts = df_long["value_raw"].str.strip().str.split(n=1, expand=True)
    value_parts.columns = ["value_token", "flag"]
    numeric_tokens = value_parts["value_token"].replace(":", pd.NA)
    value_parts["value"] = pd.to_numeric(numeric_tokens, errors="raise")
    df_long["value"] = value_parts["value"]
    df_long["flag"] = value_parts["flag"]
    df_long["year"] = df_long["year"].astype(int)
    return df_long

# %%
historical_demography = load_eurostat_data(
    "/Users/rodionbogac/Documents/GitHub/business-dynamics-bdi/data/raw/"
    "bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz"
)

# %%
economic_accounts = load_eurostat_data(
    "/Users/rodionbogac/Documents/GitHub/business-dynamics-bdi/data/raw/"
    "nama_10_a64_Gross_value_added_and_income.tsv.gz"
)
# %%
df = pd.read_csv(
    "/Users/rodionbogac/Documents/GitHub/business-dynamics-bdi/data/raw/"
    "bd_9bd_sz_cl_r2_Business_demography_by_size.tsv.gz",
    sep="\t",
    compression="gzip",
    dtype=str,
    keep_default_na=False,
)

# %%
df_clean = df.copy()
df_clean.columns = df_clean.columns.str.strip()

# %%
first_column_name = df_clean.columns[0]
dimension_names = first_column_name.split("\\")[0].split(",")

# %%
dimensions = df_clean.iloc[:, 0].str.split(",", expand=True)
dimensions.columns = dimension_names

# %%
df_wide = pd.concat([dimensions, df_clean.iloc[:, 1:]], axis=1)

# %%
df_long = df_wide.melt(
    id_vars=dimension_names,
    var_name="year",
    value_name="value_raw",
)

# %%
value_parts = df_long["value_raw"].str.strip().str.split(n=1, expand=True)
value_parts.columns = ["value_token", "flag"]

# %%
numeric_tokens = value_parts["value_token"].replace(":", pd.NA)
value_parts["value"] = pd.to_numeric(numeric_tokens, errors="raise")

# %%
df_long["value"] = value_parts["value"]
df_long["flag"] = value_parts["flag"]
df_long["year"] = df_long["year"].astype(int)

# %%
print("shape:", df_long.shape)
print("gap:", (value_parts["value_token"] == ":").sum())
print("num gap:", df_long["value"].isna().sum())
print(
    "dupl keys:",
    df_long.duplicated(
        subset=dimension_names + ["year"],
        keep=False,
    ).sum(),
)

# %%
df_long.head()
# %%
