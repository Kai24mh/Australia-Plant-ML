"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_2

Research Question:
    Can plot-level environmental conditions and species family be used together
    to predict seed production at the individual plant level?
    
Purpose:
    To evaluate whether incorporating species family alongside plot-level
    environmental predictors can explain and predict variation in individual
    plant seed production.
"""

# Libraries
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR_2 = ROOT / "figures" / "model_2"


# Load data
seeds = pd.read_csv(PROCESSED_DATA_DIR / "seeds.csv")
species = pd.read_csv(PROCESSED_DATA_DIR / "species.csv")
plots = pd.read_csv(PROCESSED_DATA_DIR / "plots.csv")



""" MERGE DATA """

# Add family information to seed observations
# Inner merge automatically removes UK.GRASS because it is not in species.csv
df = seeds.merge(
    species[["Species", "family"]],
    on="Species",
    how="inner",
    validate="many_to_one")


# Add environmental plot information
df = df.merge(
    plots,
    left_on="Plot.ID",
    right_on="Plot",
    how="left",
    validate="many_to_one")


# Report observations removed during species matching
print(f"\n{'-' * 50}\nDATA SUMMARY\n{'-' * 50}")
print(f"Total seed observations: {len(seeds)}")
print(f"Observations after species matching: {len(df)}")
print(f"Number of families: {df['family'].nunique()}")



""" PREPARE MODEL DATA """

# Environmental predictors
environmental_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"]


# One-hot encode family
family_data = pd.get_dummies(
    df["family"],
    prefix="Family",
    dtype=int)

# Add family predictors to dataframe
df = pd.concat(
    [df, family_data],
    axis=1)


# Family predictor names
family_features = family_data.columns.tolist()
features = environmental_features + family_features

# Remove rows missing required model data
model_data = df.dropna(
    subset=features + ["Num.Seed", "Plot.ID"]).copy()

# Define X, y, and groups
X = model_data[features]
y = model_data["Num.Seed"]
groups = model_data["Plot.ID"]


""" MODEL SUMMARY """

print(f"\n{'-' * 50}\nMODEL DATA\n{'-' * 50}")
print(f"Observations used in model: {len(model_data)}")
print(f"Number of plots: {groups.nunique()}")
print(f"Number of families: {model_data['family'].nunique()}")
print(f"Number of predictors: {len(features)}")



""" RANDOM FOREST MODEL """

# Grouped cross-validation
gkf = GroupKFold(n_splits=5)

r2_scores = []
mae_scores = []
rmse_scores = []
feature_importances = []


for train_index, test_index in gkf.split(X, y, groups):

    X_train = X.iloc[train_index]
    X_test = X.iloc[test_index]

    y_train = y.iloc[train_index]
    y_test = y.iloc[test_index]


    # Create model
    model = RandomForestRegressor(
        n_estimators=500,
        random_state=42,
        n_jobs=-1)


    # Train model
    model.fit(X_train, y_train)

    # Predict test data
    predictions = model.predict(X_test)

    # Performance metrics
    r2_scores.append(
        r2_score(y_test, predictions))

    mae_scores.append(
        mean_absolute_error(y_test, predictions))

    rmse_scores.append(
        np.sqrt(mean_squared_error(y_test, predictions)))


    # Save feature importance from each fold
    feature_importances.append(
        model.feature_importances_)



""" MODEL PERFORMANCE """

print(f"\n{'-' * 50}\nMODEL PERFORMANCE\n{'-' * 50}")
print(f"Mean R²: {np.mean(r2_scores):.3f}")
print(f"Mean MAE: {np.mean(mae_scores):.3f}")
print(f"Mean RMSE: {np.mean(rmse_scores):.3f}")



""" FEATURE IMPORTANCE """

# Average feature importance across folds
mean_importance = np.mean(
    feature_importances,
    axis=0)

importance_df = pd.DataFrame({
    "Variable": features,
    "Importance": mean_importance})

# Remove Family_ prefix from family names
importance_df["Variable"] = (
    importance_df["Variable"]
    .str.replace("Family_", "", regex=False))

importance_df = importance_df.sort_values(
    "Importance",
    ascending=False).reset_index(drop=True)

print(f"\n{'-' * 50}\nFEATURE IMPORTANCE\n{'-' * 50}")
print(importance_df)



""" PLOT FEATURE IMPORTANCE """

plt.figure(figsize=(10, 8))

plt.barh(
    importance_df["Variable"],
    importance_df["Importance"],
    color = "purple")

plt.xlabel("Feature Importance")
plt.ylabel("Variable")
plt.title("Model 2 Feature Importance")

plt.gca().invert_yaxis()
plt.tight_layout()

plt.savefig(
    FIGURE_DIR_2 / "family_feature_importance.png",
    dpi=300,
    bbox_inches="tight")

plt.show()