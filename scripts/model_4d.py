"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_4d

Research Question:
    How accurately does the selected Random Forest configuration predict
    VERO seed production across unseen plots, where do prediction errors
    occur, and which ecological predictors contribute most to performance?

Purpose:
    To interpret the results of Model 4c by comparing model configurations,
    examining prediction errors across individuals and plots, investigating
    high-seed observations, and evaluating ecological predictor importance
    using held-out permutation importance.
"""

# Libraries
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold



""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
RESULTS_DIR = (ROOT / "figures" / "model_4" / "model_4c")
OUTPUT_DIR = (ROOT / "figures" / "model_4" / "analysis")
OUTPUT_DIR.mkdir(parents = True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 5
N_TREES = 300

BEST_CV = "GroupKFold"
BEST_GROUP = "Functional"
BEST_TREATMENT = "Log1p"



""" LOAD RESULTS """

print(f"\n{'-' * 50}\nMODEL 4C RESULTS\n{'-' * 50}")

comparison = pd.read_csv(RESULTS_DIR / "model_4c_comparison.csv")
folds = pd.read_csv(RESULTS_DIR / "model_4c_fold_results.csv")
predictions = pd.read_csv(RESULTS_DIR / "model_4c_predictions.csv")
predictor_groups = pd.read_csv(RESULTS_DIR / "model_4c_predictor_groups.csv")

df = pd.read_csv(
    DATA_DIR / "vero_ecological_predictors.csv")

print("Configurations:", len(comparison))
print("Fold results:", len(folds))
print("Prediction records:", len(predictions))
print("VERO observations:", len(df))



""" SELECT BEST CONFIGURATION """

print(f"\n{'-' * 50}\nBEST CONFIGURATION\n{'-' * 50}")

best = predictions.loc[
    (predictions["CV"] == BEST_CV)
    & (predictions["Group"] == BEST_GROUP)
    & (predictions["Treatment"] == BEST_TREATMENT)].copy()

if best.empty:
    raise ValueError(
        "Best model predictions were not found.")

print("Validation:", BEST_CV)
print("Predictors:", BEST_GROUP)
print("Treatment:", BEST_TREATMENT)
print("Observations:", len(best))
print("Plots:", best["Plot.ID"].nunique())



""" MODEL PERFORMANCE COMPARISON """

# Compare the ten lowest-MAE configurations separately
# for KFold and GroupKFold validation
for cv_method in ["KFold", "GroupKFold"]:
    subset = comparison.loc[
        comparison["CV"] == cv_method].sort_values("Mean_MAE")

    top = subset.head(10).copy()
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = (
        top["Group"]
        + " / "
        + top["Treatment"])

    # Lower MAE indicates smaller average prediction errors
    ax.barh(
        labels[::-1],
        top["Mean_MAE"][::-1])

    ax.set_xlabel("Mean Absolute Error (Seeds)")
    ax.set_title(f"{cv_method}: Top 10 Configurations")

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR / f"{cv_method}_top_models.png",
        dpi=300)

    plt.show()
    plt.close(fig)



""" PREDICTOR GROUP COMPARISON """

# Hold validation and target treatment constant so differences
# primarily reflect the ecological predictor groups
group_comparison = comparison.loc[
    (comparison["CV"] == "GroupKFold")
    & (comparison["Treatment"] == "Original")
].sort_values("Mean_MAE")

fig, ax = plt.subplots(figsize=(10, 5))

ax.bar(
    group_comparison["Group"],
    group_comparison["Mean_MAE"],
    color = "indianred")

ax.set_title(
    "Ecological Predictor Groups: Original Target")

ax.set_ylabel("Mean Absolute Error (Seeds)")
ax.tick_params(axis="x", rotation=35)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "predictor_group_comparison.png",
    dpi = 300)

plt.show()
plt.close(fig)



""" OUTLIER TREATMENT COMPARISON """

# Compare original, IQR-filtered, and log1p treatments
treatment_comparison = comparison.loc[
    (comparison["CV"] == "GroupKFold")
    & (comparison["Group"] == BEST_GROUP)].copy()

fig, axes = plt.subplots(
    1, 3,
    figsize=(14, 4))

metrics = [
    ("Mean_R2", "Mean R²"),
    ("Mean_MAE", "Mean MAE"),
    ("Mean_RMSE", "Mean RMSE")]

for ax, (column, label) in zip(
    axes,
    metrics
):

    ax.bar(
        treatment_comparison["Treatment"],
        treatment_comparison[column])

    ax.set_title(label)
    ax.tick_params(axis="x", rotation=25)

fig.suptitle(
    "Functional Predictors: Target Treatments")

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "treatment_comparison.png",
    dpi=300)

plt.show()
plt.close(fig)



""" OBSERVED VS. PREDICTED """

# Compare observed seed counts with held-out predictions
# to identify systematic overprediction or underprediction
fig, ax = plt.subplots(figsize=(7, 6))

ax.scatter(
    best["Observed"],
    best["Predicted"],
    alpha = 0.3,
    s = 20)

maximum = max(
    best["Observed"].max(),
    best["Predicted"].max())

# Points on the diagonal represent perfect predictions
ax.plot(
    [0, maximum],
    [0, maximum],
    linestyle = "--",
    color = "tomato",
    label = "Perfect Prediction")

ax.set_xlabel("Observed VERO Seeds")
ax.set_ylabel("Predicted VERO Seeds")

ax.set_title("Functional + Log1p: Held-Out Plot Predictions")
ax.legend()
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "observed_vs_predicted.png",
    dpi=300)

plt.close(fig)



""" HIGH-SEED PREDICTION ERRORS """

print(f"\n{'-' * 50}\nANALYZING HIGH-SEED ERRORS\n{'-' * 50}")

# Match the descriptive global IQR threshold
q1 = best["Observed"].quantile(0.25)
q3 = best["Observed"].quantile(0.75)
upper = q3 + 1.5 * (q3 - q1)

# Flag high-seed observations without excluding them
best["High_Seed"] = best["Observed"] > upper

best["Residual"] = (best["Observed"] - best["Predicted"])
best["Absolute_Error"] = (best["Residual"].abs())

# Compare prediction accuracy for typical and high-seed plants
error_summary = (
    best.groupby("High_Seed")
    .agg(
        Observations = ("Observed", "size"),
        Mean_Observed = ("Observed", "mean"),
        Mean_Predicted = ("Predicted", "mean"),
        MAE = ("Absolute_Error", "mean"),
        Mean_Residual = ("Residual", "mean")
    ).reset_index())

error_summary.to_csv(
    OUTPUT_DIR / "high_seed_error_summary.csv",
    index=False)

print(error_summary.round(2).to_string(index=False))

# Visualize whether prediction errors increase with seed production
fig, ax = plt.subplots(figsize=(8, 5))

ax.scatter(
    best["Observed"],
    best["Residual"],
    alpha=0.3)

ax.axhline(
    0,
    color = "black",
    linestyle = "--")

# Mark the threshold used to classify high-seed observations
ax.axvline(
    upper,
    color = "red",
    linestyle = ":",
    label = f"IQR Upper Fence = {upper:.1f}")

ax.set_xlabel("Observed VERO Seeds")
ax.set_ylabel("Residual (Observed - Predicted)")

ax.set_title("Prediction Residuals by Seed Count")
ax.legend()

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "residuals_vs_observed.png",
    dpi=300)

plt.show()
plt.close(fig)



""" PLOT-LEVEL PERFORMANCE """

print(f"\n{'-' * 50}\nANALYZING PLOT-LEVEL PERFORMANCE\n{'-' * 50}")

# Aggregate individual prediction errors within each plot
# to identify plots where the model performs poorly
plot_errors = (
    best.groupby("Plot.ID")
    .agg(
        Observations = ("Observed", "size"),
        Mean_Observed = ("Observed", "mean"),
        Mean_Predicted = ("Predicted", "mean"),
        MAE = ("Absolute_Error", "mean"),
        Mean_Residual = ("Residual", "mean")
    ).reset_index())

plot_errors = plot_errors.sort_values(
    "MAE",
    ascending=False)

plot_errors.to_csv(
    OUTPUT_DIR / "plot_prediction_errors.csv",
    index = False)

print("\nPlots with highest MAE:\n")

print(
    plot_errors.head(10)
    .round(2)
    .to_string(index=False))

fig, ax = plt.subplots(figsize = (10, 5))
top_plots = plot_errors.head(15)

ax.bar(
    top_plots["Plot.ID"].astype(str),
    top_plots["MAE"],
    color = "orange")

ax.set_xlabel("Plot ID")
ax.set_ylabel("Mean Absolute Error (Seeds)")
ax.set_title("Plots with Highest Prediction Errors")

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "plot_prediction_errors.png",
    dpi = 300)

plt.show()
plt.close(fig)



""" HELD-OUT PERMUTATION IMPORTANCE """

features = predictor_groups.loc[
    predictor_groups["Group"] == BEST_GROUP,
    "Predictor"].tolist()

df["Num.Seed"] = pd.to_numeric(
    df["Num.Seed"],
    errors = "coerce")

df = df.dropna(
    subset = [
        "Num.Seed",
        "Plot.ID",
        "Per.Litt",
        "Per.Bare",
        "Per.Woody",
        "Soil.P",
        "Soil.Water",
        "Canopy.Cover"
    ]).copy()

df = df.loc[df["Num.Seed"] >= 0].copy()

if "Species" in df.columns:
    df = df.loc[df["Species"] == "VERO"].copy()

df = df.reset_index(drop=True)

# Keep plots separate between training and test sets
splitter = GroupKFold(
    n_splits=N_SPLITS)

importance_records = []

for fold, (train_idx, test_idx) in enumerate(
    splitter.split(
        df,
        groups=df["Plot.ID"]),
    start=1
):

    train = df.iloc[train_idx]
    test = df.iloc[test_idx]

    X_train = train[features].apply(
        pd.to_numeric,
        errors="coerce")

    X_test = test[features].apply(
        pd.to_numeric,
        errors="coerce")

    # Use only training-fold medians to fill missing values
    medians = X_train.median().fillna(0)

    X_train = X_train.fillna(medians)
    X_test = X_test.fillna(medians)

    y_train = np.log1p(train["Num.Seed"])

    model = RandomForestRegressor(
        n_estimators=N_TREES,
        random_state=RANDOM_STATE,
        n_jobs=-1)

    model.fit(X_train, y_train)

    # Importance is evaluated on the same
    # transformed target scale used for training.
    result = permutation_importance(
        model,
        X_test,
        np.log1p(test["Num.Seed"]),
        scoring="neg_mean_absolute_error",
        n_repeats=5,
        random_state=RANDOM_STATE,
        n_jobs=-1)

    for feature, importance in zip(
        features,
        result.importances_mean
    ):

        importance_records.append({
            "Fold": fold,
            "Predictor": feature,
            "Importance": importance
        })

importance_df = pd.DataFrame(importance_records)

# Average importance across folds and examine its variability
importance_summary = (
    importance_df.groupby("Predictor")
    .agg(
        Mean_Importance=("Importance", "mean"),
        SD_Importance=("Importance", "std")
    )
    .reset_index()
    .sort_values(
        "Mean_Importance",
        ascending=False
    ))

importance_df.to_csv(
    OUTPUT_DIR / "permutation_importance_folds.csv",
    index=False)

importance_summary.to_csv(
    OUTPUT_DIR / "permutation_importance_summary.csv",
    index=False)

print("\nTop predictors:\n")

print(
    importance_summary.head(15)
    .round(4)
    .to_string(index=False))

# Visualize the twelve highest-ranked predictors
top_importance = importance_summary.head(12)
fig, ax = plt.subplots(figsize = (9, 6))

ax.barh(
    top_importance["Predictor"][::-1],
    top_importance["Mean_Importance"][::-1],
    color = "olivedrab")

ax.axvline(
    0,
    color = "black",
    linewidth = 0.8)

ax.set_xlabel(
    "Permutation Importance "
    "(Increase in Log-Scale MAE)")

ax.set_title(
    "Functional Model: Held-Out Predictor Importance")

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "permutation_importance.png",
    dpi=300)

plt.show()
plt.close(fig)


""" FINAL SUMMARY """

print(f"\n{'-' * 50}\nSUMMARY\n{'-' * 50}")

print("\nBest configuration:")
print(BEST_CV, BEST_GROUP, BEST_TREATMENT)

print("\nVERO observations:", len(best))
print("Plots:", best["Plot.ID"].nunique())

print("\nHigh-seed threshold:", upper)
print("\nTop five predictors:")

print(
    importance_summary.head(5)[
        ["Predictor", "Mean_Importance"]
    ].round(4).to_string(index=False))

