"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_4b

Research Question:
    How is VERO seed production distributed across individuals and plots,
    where do extreme seed counts occur, and which ecological characteristics
    are most strongly associated with variation in seed production?

Purpose:
    To examine the distribution of VERO seed production, identify extreme
    observations using the IQR method, investigate variation among plots,
    and explore relationships between seed production and ecological
    predictors without removing any observations.
"""

# Libraries
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr


""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = (ROOT / "data" / "processed" / "vero_ecological_predictors.csv")
OUTPUT_DIR = (ROOT / "figures" / "model_4" / "model_4b")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Num.Seed"
PLOT_ID = "Plot.ID"

# Original environmental predictors
environmental_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"
]



""" LOAD AND CLEAN DATA """

df = pd.read_csv(DATA_FILE)

df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")

# Exclude missing or invalid seed counts
df = df.dropna(subset=[TARGET, PLOT_ID]).copy()
df = df.loc[df[TARGET] >= 0].copy()

print("VERO observations:", len(df))
print("VERO plots:", df[PLOT_ID].nunique())
print("Dataset columns:", len(df.columns))



""" IDENTIFY ECOLOGICAL PREDICTORS """

# Exclude response, identifiers, coordinates, and 
# other columns not intended as ecological predictors.
exclude = {
    TARGET,
    PLOT_ID,
    "Plot",
    "Species",
    "Lat",
    "Long",
    "Latitude",
    "Longitude",
    "UTM.E",
    "UTM.N",
    "Block"
}

# Recognize predictor families generated in Model 4a
prefixes = (
    "SpeciesProp_",
    "Species_",
    "LifeForm_",
    "Family_",
    "Native_",
    "Exotic_",
    "Origin_",
    "OtherSpecies_",
    "Community_",
    "VERO_"
)

additional = {
    "Other_Individuals",
    "Mean_BrayCurtis",
    "Dominant_Species_Proportion",
    "Top3_Species_Proportion",
    "Simpson_Concentration",
    "Effective_Species_Number",
    "Num.Species",
    "Num.Indivs",
    "Elevation"
}

predictors = [
    col for col in df.columns
    if col not in exclude
    and (
        col in environmental_features
        or col in additional
        or col.startswith(prefixes))]

for col in predictors:
    df[col] = pd.to_numeric(
        df[col], errors="coerce")

print("Candidate ecological predictors:", len(predictors))



""" VERO SEED DISTRIBUTION """

print(f"\n{'-' * 50}\nVERO SEED DISTRIBUTION\n{'-' * 50}")

summary = df[TARGET].describe()

print(summary)
print("Zero-seed observations:", (df[TARGET] == 0).sum())
print("Skewness:", round(df[TARGET].skew(), 3))

summary.to_csv(
    OUTPUT_DIR / "seed_distribution_summary.csv")

# Compare the original distribution with a log transformation.
# log1p accommodates zero counts and compresses high values.
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].hist(
    df[TARGET],
    bins=40,
    edgecolor = "black")

axes[0].set_title("VERO Seed Production")
axes[0].set_xlabel("Number of Seeds")
axes[0].set_ylabel("Frequency")

axes[1].hist(
    np.log1p(df[TARGET]),
    bins = 40,
    edgecolor = "black")

axes[1].set_title("Log1p-Transformed Seed Production")
axes[1].set_xlabel("log(1 + Seeds)")
axes[1].set_ylabel("Frequency")

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "seed_distribution.png",
    dpi=300)

plt.close(fig)



""" IDENTIFY IQR OUTLIERS """

print(f"\n{'-' * 50}\nIDENTIFYING IQR OUTLIERS\n{'-' * 50}")

# Calculate the middle 50% of the seed-count distribution
q1 = df[TARGET].quantile(0.25)
q3 = df[TARGET].quantile(0.75)

iqr = q3 - q1

# Observations beyond 1.5 times the IQR are flagged as extreme
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

df["IQR_Outlier"] = (
    (df[TARGET] < lower)
    | (df[TARGET] > upper))

outlier_count = df["IQR_Outlier"].sum()
outlier_percent = 100 * df["IQR_Outlier"].mean()

print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("Lower fence:", lower)
print("Upper fence:", upper)
print("Outliers:", outlier_count)
print("Outlier percentage:", round(outlier_percent, 2))

df.loc[df["IQR_Outlier"]].to_csv(
    OUTPUT_DIR / "iqr_outlier_observations.csv",
    index = False)



""" VISUALIZE IQR OUTLIERS """

# Show where the upper IQR threshold falls within
# the full distribution of VERO seed production
fig, ax = plt.subplots(figsize=(9, 5))

ax.hist(
    df[TARGET],
    bins = 40,
    edgecolor = "black")

ax.axvline(
    upper,
    color = "red",
    linestyle = "--",
    label=f"Upper IQR Fence = {upper:.1f}")

ax.set_title("VERO Seed Production and IQR Outliers")
ax.set_xlabel("Number of Seeds")
ax.set_ylabel("Frequency")
ax.legend()

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "iqr_outliers.png",
    dpi=300)

plt.show()



""" OUTLIERS BY PLOT """

print(f"\n{'-' * 50}\nOUTLIERS BY PLOT\n{'-' * 50}")

plot_summary = (
    df.groupby(PLOT_ID)
    .agg(
        Observations=(TARGET, "size"),
        Mean_Seeds=(TARGET, "mean"),
        Median_Seeds=(TARGET, "median"),
        SD_Seeds=(TARGET, "std"),
        Maximum_Seeds=(TARGET, "max"),
        Total_Seeds=(TARGET, "sum"),
        Outliers=("IQR_Outlier", "sum")
    )
    .reset_index())

# Account for differences in sample size between plots
plot_summary["Outlier_Percent"] = (100 * plot_summary["Outliers"] / plot_summary["Observations"])

plot_summary = plot_summary.sort_values(
    "Outliers",
    ascending=False)

plot_summary.to_csv(
    OUTPUT_DIR / "outliers_by_plot.csv",
    index=False)

print("\nPlots with most outliers:")
print(
    plot_summary.head(10)
    .round(2)
    .to_string(index=False))

# Visualize plots with the greatest number of flagged observations
fig, ax = plt.subplots(figsize=(12, 5))
top_plots = plot_summary.head(15)

ax.bar(
    top_plots[PLOT_ID].astype(str),
    top_plots["Outliers"])

ax.set_title("Plots with the Most VERO Outliers")
ax.set_xlabel("Plot ID")
ax.set_ylabel("Number of Outliers")

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "outliers_by_plot.png",
    dpi=300)

plt.show()



""" HIGH VS LOW SEED-PRODUCTION PLOTS """

print(f"\n{'-' * 50}\nCOMPARING HIGH AND LOW PRODUCTION PLOTS\n{'-' * 50}")

# Summarize VERO seed production at the plot level
plot_data = (
    df.groupby(PLOT_ID)[TARGET]
    .agg(
        Mean_Seeds = "mean",
        Median_Seeds = "median",
        Observations = "size"
    ))

# Add one value per plot for each predictor.
plot_predictors = (
    df.groupby(PLOT_ID)[predictors]
    .first())

plot_data = plot_data.join(plot_predictors)

# Divide plots into lower, middle, and upper
# thirds based on mean VERO seed production.
plot_data["Production_Group"] = pd.qcut(
    plot_data["Mean_Seeds"].rank(method="first"),
    q = 3,
    labels = ["Low", "Medium", "High"])

plot_data.reset_index().to_csv(
    OUTPUT_DIR / "plot_ecological_summary.csv",
    index = False)

group_means = (
    plot_data.groupby(
        "Production_Group",
        observed = True
    )[predictors]
    .mean())

group_means.to_csv(
    OUTPUT_DIR / "production_group_predictors.csv")

print("\nProduction groups:")
print(plot_data["Production_Group"].value_counts())



""" ECOLOGICAL CORRELATIONS """

print(f"\n{'-' * 50}\nECOLOGICAL CORRELATIONS\n{'-' * 50}")
correlations = []

# Test monotonic relationships between ecological predictors
# and mean VERO seed production across plots.
for predictor in predictors:

    subset = plot_data[
        [predictor, "Mean_Seeds"]].dropna()

    # Skip predictors with insufficient observations or variation
    if len(subset) < 5:
        continue

    if subset[predictor].nunique() < 2:
        continue

    rho, p_value = spearmanr(
        subset[predictor],
        subset["Mean_Seeds"])

    if not np.isfinite(rho):
        continue

    correlations.append({
        "Predictor": predictor,
        "Spearman_Rho": rho,
        "P_Value": p_value,
        "Abs_Rho": abs(rho),
        "Plots": len(subset)
    })

correlation_df = pd.DataFrame(correlations)

if correlation_df.empty:
    raise ValueError(
        "No usable predictor correlations were calculated.")

# Rank predictors by correlation strength, regardless of direction
correlation_df = correlation_df.sort_values(
    "Abs_Rho",
    ascending = False)

correlation_df.to_csv(
    OUTPUT_DIR / "ecological_correlations.csv",
    index = False)

print("\nTop 15 strongest correlations:")
print(
    correlation_df.head(15)
    .round(3)
    .to_string(index=False))



""" VISUALIZE STRONGEST RELATIONSHIPS """

top_predictors = (
    correlation_df.head(6)["Predictor"].tolist())

for predictor in top_predictors:

    subset = plot_data[
        [predictor, "Mean_Seeds"]].dropna()

    rho = correlation_df.loc[
        correlation_df["Predictor"] == predictor,
        "Spearman_Rho"].iloc[0]

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.scatter(
        subset[predictor],
        subset["Mean_Seeds"],
        alpha = 0.75)

    ax.set_xlabel(predictor)
    ax.set_ylabel("Mean VERO Seeds per Individual")

    ax.set_title(
        f"{predictor}\n"
        f"Spearman rho = {rho:.3f}")

    fig.tight_layout()

    safe_name = "".join(
        char if char.isalnum() else "_"
        for char in predictor)

    fig.savefig(
        OUTPUT_DIR / f"relationship_{safe_name}.png",
        dpi = 300)
    
    plt.show()
    plt.close(fig)



""" FINAL SUMMARY """

print(f"\n{'-' * 50}\nSUMMARY\n{'-' * 50}")

print("VERO observations:", len(df))
print("VERO plots:", df[PLOT_ID].nunique())
print("Ecological predictors examined:", len(predictors))

print("\nOUTLIERS")
print("IQR upper fence:", round(upper, 2))
print("Outlier observations:", outlier_count)
print("Outlier percentage:", round(outlier_percent, 2))

print("\nTOP ECOLOGICAL CORRELATIONS")

print(
    correlation_df[
        ["Predictor", "Spearman_Rho", "P_Value"]
    ].head(10).round(3).to_string(index=False))
