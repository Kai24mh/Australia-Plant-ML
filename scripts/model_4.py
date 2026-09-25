"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_4

Research Question:
    How does Random Forest performance for predicting VERO seed production 
    change when using standard KFold cross-validation instead of GroupKFold
    by plot?
    
Purpose:
    To evaluate the effect of cross-validation method on VERO model 
    performance by allowing individual observations from the same plot 
    to occur in both training and testing data.
"""

# Libraries
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_validate


""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR_4 = ROOT / "figures" / "model_4"
FIGURE_DIR_4.mkdir(parents=True, exist_ok=True)

# Load data
seeds = pd.read_csv(PROCESSED_DATA_DIR / "seeds.csv")
plots = pd.read_csv(PROCESSED_DATA_DIR / "plots.csv")



""" DEFINE TOP SPECIES """

top_species = ["VERO"]

seeds["Species"] = (
    seeds["Species"]
    .astype(str)
    .str.strip()
    .str.upper())

seeds = seeds[seeds["Species"].isin(top_species)].copy()

# New dataframe combining species and plots
df = seeds.merge(
    plots,
    left_on="Plot.ID",
    right_on="Plot",
    how="left",
    validate="many_to_one")

print("Total observations:", len(df))
print("Observations without matching plot data:", df["Plot"].isna().sum())



""" RESPONSE VARIABLE AND ENVIRONMENTAL PREDICTORS """

target = "Num.Seed"

numeric_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"]


# Convert variables to numeric
for column in [target] + numeric_features:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce")



""" RANDOM FOREST LOOP """

# Store results
model_results = []
importance_results = []


for species in top_species:

    print(f"\n{'-' * 50}\n{species}\n{'-' * 50}")

    # Select one species
    species_df = df[df["Species"] == species].copy()
    
    # Use for excluding outliar data
    if species == "VERO":
        exclude_plots = [56]
        species_df = species_df[
            ~species_df["Plot.ID"].isin(exclude_plots)].copy()

    # Remove rows missing required values
    species_df = species_df.dropna(
        subset=[target] + numeric_features)

    print("Observations used:", len(species_df))
    print("Number of plots:", species_df["Plot.ID"].nunique())


    # Define model data
    X = species_df[numeric_features]
    y = species_df[target]

    # Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=500,
        random_state=42,
        n_jobs=-1)

    # Standard 5-fold cross-validation
    cv = KFold(
        n_splits=5,
        shuffle=True,
        random_state=42)

    scoring = {
        "R2": "r2",
        "MAE": "neg_mean_absolute_error",
        "RMSE": "neg_root_mean_squared_error"}

    cv_results = cross_validate(
        rf_model,
        X,
        y,
        cv=cv,
        scoring=scoring)


    # Calculate performance
    mean_r2 = np.mean(cv_results["test_R2"])
    mean_mae = -np.mean(cv_results["test_MAE"])
    mean_rmse = -np.mean(cv_results["test_RMSE"])

    print("\nMODEL PERFORMANCE")
    print(f"Mean R²:   {mean_r2:.3f}")
    print(f"Mean MAE:  {mean_mae:.2f} seeds")
    print(f"Mean RMSE: {mean_rmse:.2f} seeds")


    # Save results
    model_results.append({
        "Species": species,
        "Observations": len(species_df),
        "Plots": species_df["Plot.ID"].nunique(),
        "R2": round(mean_r2, 3),
        "MAE": round(mean_mae, 2),
        "RMSE": round(mean_rmse, 2)})


    # Fit model using full dataset
    rf_model.fit(X, y)


    # Feature importance
    importance = pd.DataFrame({
        "Species": species,
        "Variable": numeric_features,
        "Importance":
            rf_model.feature_importances_})

    importance["Importance"] = importance["Importance"].round(3)
    importance = importance.sort_values(
        "Importance",
        ascending=False)

    print("\nFEATURE IMPORTANCE")
    print(
        importance[
            ["Variable", "Importance"]
        ].to_string(index=False))

    importance_results.append(importance)


    """ PLOTTING """

    # Plot feature importance for species
    plt.figure(figsize=(8, 5))

    plt.barh(
        importance["Variable"],
        importance["Importance"],
        color="darkseagreen")

    plt.xlabel("Random Forest Importance")
    plt.ylabel("Environmental Variable")
    plt.title(f"{species} Environmental Predictors of Seed Production")

    plt.gca().invert_yaxis()
    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR_4 / f"{species}_feature_importance.png",
        dpi=300,
        bbox_inches="tight")

    plt.show()



# Compare model performance
results_df = pd.DataFrame(model_results)

print(f"\n{'-' * 50}\nSPECIES COMPARISON\n{'-' * 50}")
print(results_df.to_string(index=False))