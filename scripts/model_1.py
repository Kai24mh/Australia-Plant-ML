"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_1

Research Question:
    Can plot-level environmental conditions and species identity be used together
    to predict seed production at the individual plant level?
    
Purpose:
    To evaluate whether incorporating species identity alongside plot-level
    environmental predictors improves the ability to explain and predict variation
    in individual plant seed production.
"""

# Libraries
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline



""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR_1 = ROOT / "figures" / "model_1"
FIGURE_DIR_1.mkdir(parents = True, exist_ok = True)

# Load data
seeds = pd.read_csv(PROCESSED_DATA_DIR / "seeds.csv")
plots = pd.read_csv(PROCESSED_DATA_DIR / "plots.csv")



""" MERGING SEED DATA WITH PLOT ENVIRONMENTAL DATA """

df = seeds.merge(
    plots,
    left_on="Plot.ID",
    right_on="Plot",
    how="left",
    validate="many_to_one")

print("Total seed observations:", len(df))
unmatched = df["Plot"].isna().sum()
print("Seed observations without matching plot data:", unmatched)



""" RESPONSE VARIABLE AND ENVIRONMENTAL PREDICTORS """

target = "Num.Seed"

numeric_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"]

categorical_features = ["Species"]



""" PREPARE MODEL DATA """

model_df = df[["Plot.ID", target, "Species"] + numeric_features].copy()

# Convert seed counts and environmental variables to numeric
for column in [target] + numeric_features:
    model_df[column] = pd.to_numeric(
        model_df[column],
        errors="coerce")


# Remove rows that are missing required values
model_df = model_df.dropna(
    subset=[target, "Species"] + numeric_features)

print("\nObservations used in model:", len(model_df))
print("Number of plots:", model_df["Plot.ID"].nunique())
print("Number of species:", model_df["Species"].nunique())



""" DEFINE PLOT GROUPS """

features = numeric_features + categorical_features
X = model_df[features]
y = model_df[target]
groups = model_df["Plot.ID"]


# Numeric variables are left unchanged
# Species is converted into one-hot encoded columns
preprocessor = ColumnTransformer(
    transformers = [
            ("numeric","passthrough", numeric_features),
            ("species", OneHotEncoder(
                handle_unknown = "ignore"),
            categorical_features)])



""" RANDOM FOREST MODEL """
 
rf_model = RandomForestRegressor(
    n_estimators=500,
    random_state=42,
    n_jobs=-1)

# Combine preprocessing and Random Forest model
model = Pipeline(
    steps = [
        ("preprocessor", preprocessor),
        ("random_forest", rf_model)])

cv = GroupKFold(n_splits=5)

scoring = {
    "R2": "r2",
    "MAE": "neg_mean_absolute_error",
    "RMSE": "neg_root_mean_squared_error"}

cv_results = cross_validate(
    model,
    X,
    y,
    groups=groups,
    cv=cv,
    scoring=scoring)



""" MODEL PERFORMANCE """

mean_r2 = np.mean(cv_results["test_R2"])
mean_mae = -np.mean(cv_results["test_MAE"])
mean_rmse = -np.mean(cv_results["test_RMSE"])

print(f"\n{'-' * 50}\nMODEL PERFORMANCE\n{'-' * 50}")
print(f"Mean R²:   {mean_r2:.3f}")
print(f"Mean MAE:  {mean_mae:.2f} seeds")
print(f"Mean RMSE: {mean_rmse:.2f} seeds")

model.fit(X, y)


feature_names = model["preprocessor"].get_feature_names_out()

# Remove prefixes such as "numeric_" and "species_"
feature_names = [
    name.replace("species_", "")
        .replace("Species_", "")
        .replace("numeric__", "")
        .replace("_", " ")
    for name in feature_names]


""" RESULTS """

# Feature importance
importance = pd.DataFrame({
    "Variable": feature_names,
    "Importance": model[
        "random_forest"
    ].feature_importances_})

importance["Importance"] = importance["Importance"].round(3)
importance = importance.sort_values("Importance", ascending=False)

print(f"\n{'-' * 50}\nFEATURE IMPORTANCE\n{'-' * 50}")
print(importance)



""" PLOTTING """

# Limit variables viewed
plot_importance = importance[importance["Importance"] > 0.01]

plt.figure(figsize=(10, 6))

plt.bar(
    plot_importance["Variable"],
    plot_importance["Importance"],
    color = "darkred")

plt.xticks(rotation=70)
plt.xlim(-0.5, len(plot_importance) - 0.5)
plt.xlabel("Predictor")
plt.ylabel("Random Forest Importance")
plt.title("Species and Environmental Predictors of Seed Production")
plt.tight_layout()


# Save figure for interpretation
plt.savefig(
    FIGURE_DIR_1 / "seeds_feature_importance.png",
    dpi = 300,
    bbox_inches = "tight")

plt.show()

