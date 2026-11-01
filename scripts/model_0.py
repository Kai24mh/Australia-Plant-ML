"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_0

Research Question:
    Can plot-level environmental conditions be used to predict bud production 
    at the individual plant level?
    
Purpose:
    To establish an initial machine-learning framework for evaluating whether
    variation in plot-level environmental conditions can explain and predict 
    differences in individual plant bud production.
"""

# Libraries
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, cross_validate



""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR_0 = ROOT / "figures" / "model_0"
FIGURE_DIR_0.mkdir(parents=True, exist_ok=True)

# Load data
buds = pd.read_csv(PROCESSED_DATA_DIR / "buds.csv")
plots = pd.read_csv(PROCESSED_DATA_DIR / "plots.csv")



""" MERGING PLANT DATA WITH PLOT ENVIRONMENTAL DATA """

df = buds.merge(
    plots,
    left_on="ID",
    right_on="Name",
    how="left",
    validate="many_to_one")


# Check how well the datasets matched
print("Total plant observations:", len(df))

unmatched = df["Name"].isna().sum()
print("Plants without matching plot data:", unmatched)

if unmatched > 0:
    print("\nUnmatched plot IDs:")
    print(df.loc[df["Name"].isna(), "ID"].unique())



""" RESPONSE VARIABLE AND ENVIRONMENTAL PREDICTORS """

# Response
target = "buds"

# Plot-level predictors
features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"]



""" DATA CLEANING """

# Keep only columns needed for Model 0
model_df = df[["ID", target] + features].copy()

# Convert predictors and buds to numeric
for column in [target] + features:
    model_df[column] = pd.to_numeric(
        model_df[column],
        errors="coerce")

# Remove missing buds or predictor values
model_df = model_df.dropna(
    subset=[target] + features)

print("\nObservations used in model:", len(model_df))
print("Number of plots:", model_df["ID"].nunique())



""" DEFINE PLOT GROUPS """

X = model_df[features]
y = model_df[target]

# Plants from the same plot must stay together during cross-validation
groups = model_df["ID"]



""" RANDOM FOREST MODEL """

rf_model = RandomForestRegressor(
    n_estimators=500,
    random_state=42,
    n_jobs=-1)

cv = GroupKFold(n_splits=5)

scoring = {
    "R2": "r2",
    "MAE": "neg_mean_absolute_error",
    "RMSE": "neg_root_mean_squared_error"}

cv_results = cross_validate(
    rf_model,
    X,
    y,
    groups=groups,
    cv=cv,
    scoring=scoring)



""" RESULTS """

# Model performance
mean_r2 = np.mean(cv_results["test_R2"])
mean_mae = -np.mean(cv_results["test_MAE"])
mean_rmse = -np.mean(cv_results["test_RMSE"])

print(f"\n{'-' * 50}\nMODEL PERFORMANCE\n{'-' * 50}")
print(f"Mean R²:   {mean_r2:.3f}")
print(f"Mean MAE:  {mean_mae:.2f} buds")
print(f"Mean RMSE: {mean_rmse:.2f} buds")

rf_model.fit(X, y)

# Feature importance
importance = pd.DataFrame({
    "Variable": features,
    "Importance": rf_model.feature_importances_})

importance["Importance"] = importance["Importance"].round(3)
importance = importance.sort_values(
    "Importance",
    ascending=False)

print(f"\n{'-' * 50}\nFEATURE IMPORTANCE\n{'-' * 50}")
print(importance)



""" PLOTTING """

# Feature importance plotted
plt.figure(figsize=(8, 5))

plt.barh(
    importance["Variable"],
    importance["Importance"])

plt.xlabel("Random Forest Importance")
plt.ylabel("Environmental Variable")
plt.title("Environmental Predictors of Bud Production")

plt.gca().invert_yaxis()
plt.tight_layout()

plt.savefig(
    FIGURE_DIR_0 / "buds_feature_importance.png",
    dpi=300,
    bbox_inches="tight")

plt.show()