"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_5

Research Question:
    How does the performance of different machine learning algorithms
    compare when predicting VERO seed production using environmental
    variables?

Purpose:
    To compare multiple regression algorithms for predicting VERO seed
    production and determine whether alternative modeling approaches
    improve predictive performance compared with Random Forest.
"""


# Libraries
from pathlib import Path
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor
)
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, cross_validate
from sklearn.inspection import permutation_importance


""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR_5 = ROOT / "figures" / "model_5"
FIGURE_DIR_5.mkdir(parents=True, exist_ok=True)

# Load VERO observations with ecological predictors from Model 4a
df = pd.read_csv(PROCESSED_DATA_DIR / "vero_ecological_predictors.csv")


""" SELECT VERO """

# Standardize species codes
if "Species" in df.columns:

    df["Species"] = (
        df["Species"]
        .astype(str)
        .str.strip()
        .str.upper())

    df = df.loc[
        df["Species"] == "VERO"
    ].copy()

print(f"\n{'-' * 50}\nVERO DATA\n{'-' * 50}")

print("Total VERO observations:", len(df))
print("Number of plots:", df["Plot.ID"].nunique())


""" RESPONSE VARIABLE AND ECOLOGICAL PREDICTORS """

target = "Num.Seed"

# Six environmental predictors from previous models
environmental_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"
]

# Three functional predictors selected from Model 4d
functional_features = [
    "LifeForm_Shannon",
    "LifeForm_Prop_annual.graminoid",
    "LifeForm_Prop_annual.forb"]

# Fixed predictor set for all machine learning algorithms
numeric_features = (
    environmental_features
    + functional_features)

# Verify all selected predictors exist in the dataset
missing = [
    column for column in numeric_features
    if column not in df.columns]

if missing:
    raise ValueError(
        f"Missing ecological predictors: {missing}")

# Convert target and predictors to numeric values
for column in [target] + numeric_features:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce")

# Treat infinite values as missing
df[numeric_features] = df[numeric_features].replace(
    [np.inf, -np.inf],
    np.nan)

# Remove observations with missing required values
df = df.dropna(
    subset = [target, "Plot.ID"] + numeric_features).copy()

# Seed production cannot be negative
df = df.loc[df[target] >= 0].copy()

df = df.reset_index(drop=True)

print("\nObservations used:", len(df))
print("Number of plots:", df["Plot.ID"].nunique())
print("Number of predictors:", len(numeric_features))

print("\nPredictors used:")
for feature in numeric_features:
    print(" -", feature)

# Verify that enough observations exist for cross-validation
if len(df) < 5:
    raise ValueError(
        "At least five observations are required for KFold.")



""" DEFINE MODEL DATA """

# All algorithms use the same nine ecological predictors
X = df[numeric_features]

# Individual VERO seed production
y = df[target]



""" DEFINE CROSS-VALIDATION """

# Standard 5-fold cross-validation
# Matches the original Model 5 evaluation method
cv = KFold(
    n_splits=5,
    shuffle=True,
    random_state=42)

# Performance metrics
scoring = {
    "R2": "r2",
    "MAE": "neg_mean_absolute_error",
    "RMSE": "neg_root_mean_squared_error"}



""" NEGATIVE BINOMIAL REGRESSION """

class NegativeBinomialRegressor(
    RegressorMixin,
    BaseEstimator
):

    def __init__(self, maxiter=200):
        self.maxiter = maxiter

    def fit(self, X, y):

        # Convert data to NumPy arrays
        X = np.asarray(X)
        y = np.asarray(y)

        # Add intercept
        X = sm.add_constant(
            X,
            has_constant="add")

        # Fit Negative Binomial regression
        self.model_ = sm.NegativeBinomial(
            y,
            X
        ).fit(
            disp = False,
            maxiter = self.maxiter)

        # Check whether optimization converged
        if not self.model_.mle_retvals.get(
            "converged", False
        ):
            raise RuntimeError(
                "Negative Binomial regression did not converge.")
        return self

    def predict(self, X):

        # Convert predictors to NumPy array
        X = np.asarray(X)

        X = sm.add_constant(
            X,
            has_constant="add")

        # Predict expected seed counts
        predictions = self.model_.predict(X)
        return np.maximum(predictions, 0)



""" DEFINE MACHINE LEARNING MODELS """

# All models use the same predictors and cross-validation folds
models = {

    "Linear Regression":
        Pipeline([
            ("scaler", StandardScaler()),
            ("linear", LinearRegression())
        ]),

    "Random Forest":
        RandomForestRegressor(
            n_estimators = 500,
            criterion = "squared_error",
            random_state = 42,
            n_jobs = -1
        ),

    "Random Forest (Poisson)":
        RandomForestRegressor(
            n_estimators = 500,
            criterion = "poisson",
            random_state = 42,
            n_jobs = -1
        ),

    "Negative Binomial Regression":
        Pipeline([
            ("scaler", StandardScaler()),
            ("negative_binomial",
                NegativeBinomialRegressor(
                    maxiter=200))
        ]),

    "Gradient Boosting":
        GradientBoostingRegressor(
            n_estimators = 100,
            random_state = 42),

    "Extra Trees":
        ExtraTreesRegressor(
            n_estimators = 500,
            random_state = 42,
            n_jobs = -1),

    "K-Nearest Neighbors":
        Pipeline([
            ("scaler", StandardScaler()),
            ("knn",
                KNeighborsRegressor(
                    n_neighbors=5))
        ])}



""" RUN MODEL COMPARISON """

# Store model results
model_results = []

for model_name, model in models.items():

    print(f"\n{'-' * 50}\n{model_name.upper()}\n{'-' * 50}")
      
    try:

        # Standard KFold cross-validation
        # Each model is evaluated on the same five folds
        with warnings.catch_warnings():

            warnings.simplefilter(
                "error",
                RuntimeWarning)

            cv_results = cross_validate(
                model,
                X,
                y,
                cv=cv,
                scoring=scoring,
                error_score="raise")

        # Calculate average model performance
        mean_r2 = np.mean(cv_results["test_R2"])
        mean_mae = -np.mean(cv_results["test_MAE"])
        mean_rmse = -np.mean(cv_results["test_RMSE"])

        # Print performance
        print(f"Mean R²:   {mean_r2:.3f}")
        print(f"Mean MAE:  {mean_mae:.2f} seeds")
        print(f"Mean RMSE: {mean_rmse:.2f} seeds")

        # Save results
        model_results.append({
            "Model": model_name,
            "R2": round(mean_r2, 3),
            "MAE": round(mean_mae, 2),
            "RMSE": round(mean_rmse, 2),
            "Status": "Success"})

    except Exception as error:

        # Record failed models without stopping the comparison
        print(f"Model failed: {error}")

        model_results.append({
            "Model": model_name,
            "R2": np.nan,
            "MAE": np.nan,
            "RMSE": np.nan,
            "Status": "Failed"})



""" MODEL COMPARISON """

# Convert results to DataFrame
results_df = pd.DataFrame(model_results)

# Sort models from highest to lowest R2
results_df = results_df.sort_values(
    "R2",
    ascending=False,
    na_position="last").reset_index(drop=True)

print(f"\n{'-' * 50}\nMODEL COMPARISON\n{'-' * 50}")
print(results_df.to_string(index=False))

# Save comparison results
results_df.to_csv(
    FIGURE_DIR_5 / "model_5_comparison.csv",
    index=False)

# Exclude failed models from plots
plot_results = results_df.loc[
    results_df["Status"] == "Success"].copy()



""" PLOT R-SQUARED COMPARISON """

plt.figure(figsize = (9, 5))

plt.bar(
    plot_results["Model"],
    plot_results["R2"],
    color="darkseagreen")

# Zero reference line
plt.axhline(
    y = 0,
    color = "black",
    linestyle = "--",
    linewidth = 1)

plt.ylabel("Mean R²")
plt.xlabel("Machine Learning Algorithm")
plt.title("VERO Model Performance by Machine Learning Algorithm")

plt.xticks(
    rotation = 30,
    ha = "right")

plt.tight_layout()

plt.savefig(
    FIGURE_DIR_5 / "VERO_algorithm_R2_comparison.png",
    dpi = 300,
    bbox_inches = "tight")

plt.show()



""" PLOT MAE COMPARISON """

plt.figure(figsize=(9, 5))

plt.bar(
    plot_results["Model"],
    plot_results["MAE"],
    color="darkseagreen")

plt.ylabel("Mean MAE (Seeds)")
plt.xlabel("Machine Learning Algorithm")
plt.title("VERO Mean Absolute Error by Machine Learning Algorithm")

plt.xticks(
    rotation = 30,
    ha = "right")

plt.tight_layout()

plt.savefig(
    FIGURE_DIR_5 / "VERO_algorithm_MAE_comparison.png",
    dpi = 300,
    bbox_inches = "tight")

plt.show()



""" PLOT RMSE COMPARISON """

plt.figure(figsize = (9, 5))

plt.bar(
    plot_results["Model"],
    plot_results["RMSE"],
    color="darkseagreen")

plt.ylabel("Mean RMSE (Seeds)")
plt.xlabel("Machine Learning Algorithm")
plt.title("VERO Root Mean Squared Error by Machine Learning Algorithm")

plt.xticks(
    rotation = 30,
    ha = "right")

plt.tight_layout()

plt.savefig(
    FIGURE_DIR_5 / "VERO_algorithm_RMSE_comparison.png",
    dpi = 300,
    bbox_inches = "tight")

plt.show()



""" CROSS-VALIDATED PERMUTATION FEATURE IMPORTANCE """

# Measure the decrease in held-out R² when each predictor is shuffled.
importance_rows = []

for model_name, model in models.items():

    # Only evaluate models that completed the original comparison
    model_status = results_df.loc[
        results_df["Model"] == model_name, "Status"].iloc[0]

    if model_status != "Success":
        continue

    print(f"\nPermutation importance: {model_name}")

    for fold_number, (train_idx, test_idx) in enumerate(cv.split(X, y), 1):
        fitted_model = clone(model)

        try:
            # Fit on training data only; measure importance on held-out data
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                fitted_model.fit(X.iloc[train_idx], y.iloc[train_idx])

                importance = permutation_importance(
                    fitted_model,
                    X.iloc[test_idx],
                    y.iloc[test_idx],
                    scoring="r2",
                    n_repeats=10,
                    random_state=42,
                    n_jobs=1)

            for feature, mean_score in zip(
                numeric_features, importance.importances_mean):
                importance_rows.append({
                    "Model": model_name,
                    "Fold": fold_number,
                    "Feature": feature,
                    "Importance": mean_score})

        except Exception as error:
            print(f"  Fold {fold_number} skipped: {error}")

if importance_rows:
    importance_df = pd.DataFrame(importance_rows)

    # Mean and standard deviation across all successful fold scores
    importance_summary = (
        importance_df.groupby(["Model", "Feature"])["Importance"]
        .agg(Mean_Importance="mean", SD_Importance="std", Folds="count")
        .reset_index())

    importance_summary.to_csv(
        FIGURE_DIR_5 / "VERO_permutation_importance.csv",
        index=False)

    print("\nCROSS-VALIDATED PERMUTATION IMPORTANCE (R² decrease)")
    for model_name in models:
        subset = importance_summary.loc[
            importance_summary["Model"] == model_name
        ].sort_values("Mean_Importance", ascending=False)

        if subset.empty:
            continue

        print(f"\n{model_name}")
        print(subset[["Feature", "Mean_Importance", "SD_Importance", "Folds"]]
              .to_string(index=False))

        # Plot a separate ranked importance chart for each algorithm
        ordered = subset.sort_values("Mean_Importance")
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(ordered["Feature"], ordered["Mean_Importance"],
                color="powderblue")
        ax.axvline(0, color="black", linewidth=1)
        ax.set_xlabel("Mean decrease in held-out R² after permutation")
        ax.set_title(f"VERO Feature Importance: {model_name}")
        fig.tight_layout()
        safe_name = model_name.lower().replace(" ", "_").replace(
            "(", "").replace(")", "")
        fig.savefig(
            FIGURE_DIR_5 / f"VERO_importance_{safe_name}.png",
            dpi=300, bbox_inches="tight")
        plt.show()
        plt.close(fig)
else:
    print("\nNo permutation importance results could be calculated.")



""" FINAL SUMMARY """

print(f"\n{'-' * 50}\nSUMMARY\n{'-' * 50}")

print("VERO observations:", len(df))
print("Number of plots:", df["Plot.ID"].nunique())
print("Predictors:", len(numeric_features))
print("Algorithms compared:", len(models))
print("Cross-validation: KFold (5 folds)")

if not plot_results.empty:

    best_model = plot_results.iloc[0]

    print("\nHighest mean R²:")
    print(best_model["Model"])
    print(f"R²: {best_model['R2']:.3f}")
    print(f"MAE: {best_model['MAE']:.2f} seeds")
    print(f"RMSE: {best_model['RMSE']:.2f} seeds")
