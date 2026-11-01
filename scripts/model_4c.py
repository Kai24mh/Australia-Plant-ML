"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_4c

Research Question:
    Which groups of ecological predictors most improve Random Forest
    predictions of VERO seed production, and how do target transformations,
    outlier treatments, and cross-validation methods affect model performance?

Purpose:
    To compare Random Forest performance across environmental and ecological
    predictor groups using original, IQR-filtered, and log-transformed seed
    counts under KFold and GroupKFold cross-validation, identifying the
    most promising configurations for further analysis.
"""

# Libraries
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GroupKFold
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error)



""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = (ROOT / "data" / "processed" / "vero_ecological_predictors.csv")
OUTPUT_DIR = (ROOT / "figures" / "model_4" / "model_4c")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)



""" SETTINGS """

TARGET = "Num.Seed"
PLOT_ID = "Plot.ID"

# Fixed settings make model comparisons reproducible
RANDOM_STATE = 42
N_SPLITS = 5
N_TREES = 300

# Compare random observation splits with splits that keep plots separat
CV_METHODS = [
    "KFold",
    "GroupKFold"]

# Compare approaches to handling the skewed seed distribution
treatments = [
    "Original",
    "IQR-filtered",
    "Log1p"]

environmental_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"]



""" LOAD DATA """

# Load the VERO dataset containing predictors created in Model 4a
df = pd.read_csv(DATA_FILE)
df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")

df = df.dropna(subset=[TARGET, PLOT_ID] + environmental_features).copy()
df = df.loc[df[TARGET] >= 0].copy()

# Ensure only VERO observations are used as prediction targets
if "Species" in df.columns:
    df = df.loc[
        df["Species"] == "VERO"].copy()

df = df.reset_index(drop=True)

print("VERO observations:", len(df))
print("VERO plots:", df[PLOT_ID].nunique())

if df[PLOT_ID].nunique() < N_SPLITS:
    raise ValueError("Not enough plots for GroupKFold.")



""" DEFINE PREDICTOR GROUPS """

print(f"\n{'-' * 50}\nPREDICTOR GROUPS\n{'-' * 50}")

# Find predictors belonging to a specific ecological category
def matching_columns(prefix):
    return [
        col for col in df.columns
        if col.startswith(prefix)]

functional = matching_columns("LifeForm_")
family = matching_columns("Family_")
species_composition = matching_columns("SpeciesProp_")

# Diversity describes species richness and abundance distribution
diversity = [
    "Species_Richness",
    "Species_Shannon",
    "Species_Simpson",
    "Species_Evenness"]

# Competition variables describe the surrounding non-VERO community
competition = [
    "Other_Individuals",
    "OtherSpecies_Richness",
    "OtherSpecies_Shannon",
    "OtherSpecies_Simpson",
    "OtherSpecies_Proportion"]

# Dominance measures whether a few species account for most individuals
dominance = [
    "Dominant_Species_Proportion",
    "Top3_Species_Proportion"]

combined = (
    functional
    + diversity
    + competition
    + dominance)

# Tests whether adding ecological information improves prediction
groups = {
    "Baseline": environmental_features,
    "Functional": environmental_features + functional,
    "Family": environmental_features + family,
    "Species composition":
        environmental_features + species_composition,
    "Diversity": environmental_features + diversity,
    "Competition": environmental_features + competition,
    "Combined": environmental_features + combined}

# Remove duplicates and check that predictors exist.
for name, features in groups.items():

    groups[name] = list(
        dict.fromkeys(features))

    missing = [
        col for col in groups[name]
        if col not in df.columns]

    if missing:
        raise ValueError(
            f"{name} missing columns: {missing}")

    print(f"{name}: {len(groups[name])} predictors")

group_records = []

for name, features in groups.items():
    for feature in features:

        group_records.append({
            "Group": name,
            "Predictor": feature})

pd.DataFrame(group_records).to_csv(
    OUTPUT_DIR / "model_4c_predictor_groups.csv",
    index=False)



""" METRICS AND MODEL FUNCTION """

# Evaluate predictions using the original number of seeds
def calculate_metrics(actual, predicted):
    return {
        "R2": r2_score(actual, predicted),
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(
            mean_squared_error(actual, predicted))}

# Create a new Random Forest for each cross-validation fold
def make_model():
    return RandomForestRegressor(
        n_estimators=N_TREES,
        random_state=RANDOM_STATE,
        n_jobs=-1)



""" CROSS-VALIDATION FUNCTION """

def evaluate_model(
    data,
    features,
    group_name,
    cv_method,
    treatment
):

    fold_results = []
    predictions = []

    if cv_method == "GroupKFold":
        splitter = GroupKFold(n_splits=N_SPLITS)

        splits = splitter.split(
            data,groups=data[PLOT_ID]) 

    else:
        splitter = KFold(
            n_splits=N_SPLITS,
            shuffle=True,
            random_state=RANDOM_STATE)

        splits = splitter.split(data)

    # Train and evaluate the model separately on each fold
    for fold, (train_idx, test_idx) in enumerate(
        splits,
        start=1
    ):

        train = data.iloc[train_idx].copy()
        test = data.iloc[test_idx].copy()


        """ Prepare predictors """
        
        # Select the ecological predictors for this configuration
        X_train = train[features].apply(
            pd.to_numeric,
            errors="coerce")

        X_test = test[features].apply(
            pd.to_numeric,
            errors="coerce")

        # Use training-fold medians for missing values.
        medians = X_train.median().fillna(0)

        X_train = X_train.fillna(medians)
        X_test = X_test.fillna(medians)

        y_train = train[TARGET]
        y_test = test[TARGET]


        """ IQR outlier treatment """

        if treatment == "IQR-filtered":

            q1 = y_train.quantile(0.25)
            q3 = y_train.quantile(0.75)

            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            keep = (
                (y_train >= lower)
                & (y_train <= upper))

            X_train = X_train.loc[keep]
            y_train = y_train.loc[keep]


        """ Train Random Forest """

        model = make_model()

        # Fit on transformed seed counts to reduce the influence
        # of large values, then convert predictions back to seeds
        if treatment == "Log1p":
            model.fit(
                X_train,
                np.log1p(y_train))

            predicted = np.expm1(
                model.predict(X_test))

        else:
            model.fit(X_train, y_train)
            predicted = model.predict(X_test)

        # Seed production cannot be negative
        predicted = np.maximum(predicted, 0)


        """ Evaluate """

        metrics = calculate_metrics(
            y_test,
            predicted)

        fold_results.append({
            "CV": cv_method,
            "Group": group_name,
            "Treatment": treatment,
            "Fold": fold,
            "Train_N": len(y_train),
            "Test_N": len(y_test),
            **metrics
        })


        """ Store individual predictions """

        for row_id, plot_id, actual, pred in zip(
            test.index,
            test[PLOT_ID],
            y_test,
            predicted
        ):

            predictions.append({
                "CV": cv_method,
                "Group": group_name,
                "Treatment": treatment,
                "Fold": fold,
                "Row_ID": row_id,
                "Plot.ID": plot_id,
                "Observed": actual,
                "Predicted": pred,
                "Absolute_Error": abs(actual - pred)
            })

    return (
        pd.DataFrame(fold_results),
        pd.DataFrame(predictions))



""" RUN MODEL COMPARISONS """

print(f"\n{'-' * 50}\nMODEL COMPARISONS\n{'-' * 50}")

all_folds = []
all_predictions = []

# Calculate the number of configurations and model fits
total = (
    len(groups)
    * len(CV_METHODS)
    * len(treatments))

completed = 0

print("Configurations:", total)
print("Total model fits:", total * N_SPLITS)

# Test every predictor group under both validation methods
# and all three seed-count treatments
for cv_method in CV_METHODS:
    for group_name, features in groups.items():
        for treatment in treatments:
            completed += 1

            print(
                f"\n[{completed}/{total}] "
                f"{cv_method} | "
                f"{group_name} | "
                f"{treatment}"
            )

            folds, preds = evaluate_model(
                data = df,
                features = features,
                group_name = group_name,
                cv_method = cv_method,
                treatment = treatment)

            all_folds.append(folds)
            all_predictions.append(preds)

            print(
                f"R2: {folds['R2'].mean():.3f} | "
                f"MAE: {folds['MAE'].mean():.3f} | "
                f"RMSE: {folds['RMSE'].mean():.3f}")



""" SAVE RESULTS """

fold_results = pd.concat(
    all_folds,
    ignore_index = True)

prediction_results = pd.concat(
    all_predictions,
    ignore_index = True)

comparison = (
    fold_results.groupby(
        ["CV", "Group", "Treatment"],
        as_index=False)
    .agg(
        Mean_R2 = ("R2", "mean"),
        SD_R2 = ("R2", "std"),
        Mean_MAE = ("MAE", "mean"),
        SD_MAE = ("MAE", "std"),
        Mean_RMSE = ("RMSE", "mean"),
        SD_RMSE = ("RMSE", "std")))

comparison = comparison.sort_values(["CV", "Mean_MAE"])

fold_results.to_csv(
    OUTPUT_DIR / "model_4c_fold_results.csv", index = False)

prediction_results.to_csv(
    OUTPUT_DIR / "model_4c_predictions.csv", index = False)

comparison.to_csv(
    OUTPUT_DIR / "model_4c_comparison.csv", index = False)



""" BEST CONFIGURATIONS """

print(f"\n{'-' * 50}\nBEST CONFIGURATIONS\n{'-' * 50}")

for cv_method in CV_METHODS:

    selected = comparison.loc[
        comparison["CV"] == cv_method
    ].sort_values("Mean_MAE")

    print(f"\n{cv_method}")
    print(
        selected.head(10)
        .round(3)
        .to_string(index=False))



""" FINAL SUMMARY """

print(f"\n{'-' * 50}\nSUMMARY\n{'-' * 50}")

print("VERO observations:", len(df))
print("VERO plots:", df[PLOT_ID].nunique())

print("Predictor groups:", len(groups))
print("Treatments:", len(treatments))
print("Validation methods:", len(CV_METHODS))
