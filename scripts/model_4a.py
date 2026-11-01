"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: model_4a

Research Question:
    What additional ecological characteristics can be derived from plot-level
    community composition to better describe the environmental and biological
    conditions associated with VERO seed production?

Purpose:
    To create plot-level ecological predictors describing species diversity,
    functional composition, taxonomic composition, community dominance, and
    potential competition, expanding the environmental dataset available
    for subsequent VERO seed production analyses.
"""

# Libraries
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.spatial.distance import pdist, squareform



""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "figures" / "model_4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Original environmental predictors
environmental_features = [
    "Per.Litt",
    "Per.Bare",
    "Per.Woody",
    "Soil.P",
    "Soil.Water",
    "Canopy.Cover"
]



""" FUNCTIONS """

# Standardize plot IDs for merging
def normalize_ids(values):
    
    values = values.astype("string").str.strip()
    numbers = pd.to_numeric(values, errors="coerce")

    # Convert numeric IDs to integers when possible
    if numbers.notna().all():
        if np.allclose(numbers, np.round(numbers)):
            return numbers.astype("Int64").astype(str)

    return values


# Calculate Shannon, Simpson, richness, evenness
def diversity_metrics(counts):

    totals = counts.sum(axis=1)
    proportions = counts.div(
        totals.replace(0, np.nan),
        axis=0).fillna(0)

    # Shannon: diversity accounting for richness and relative abundance
    shannon = -(proportions * np.log(proportions.where(proportions > 0, 1))
    ).sum(axis = 1)

    # Simpson: probability that two randomly selected individuals
    # belong to different species or groups
    simpson = 1 - (proportions ** 2).sum(axis=1)
    
    # Richness: number of species or groups present
    richness = (counts > 0).sum(axis=1)

    # Evenness: how evenly individuals are distributed among groups
    evenness = pd.Series(
        np.where(
            richness > 1, shannon / np.log(richness.clip(lower = 2)), 0),
        index=counts.index)

    return pd.DataFrame({
        "Richness": richness,
        "Shannon": shannon,
        "Simpson": simpson,
        "Evenness": evenness})


# Summarize community composition by life form or taxonomic family
def attribute_composition(counts, species_info, column, prefix):

    if column not in species_info.columns:
        print(f"Skipping {column}: not found.")
        return pd.DataFrame(index=counts.index)

    mapping = (
        species_info.set_index("Species")[column]
        .astype("string")
        .str.strip())

    mapping = mapping.reindex(counts.columns)
    valid = mapping.notna() & mapping.ne("")

    if not valid.any():
        return pd.DataFrame(index=counts.index)

     # Combine species abundances belonging to the same group
    grouped = (
        counts.loc[:, valid]
        .T.groupby(mapping.loc[valid])
        .sum()
        .T)

     # Calculate each group's proportion of classified individuals
    totals = grouped.sum(axis=1)
    proportions = grouped.div(totals.replace(0, np.nan), axis=0).fillna(0)

    result = proportions.add_prefix(f"{prefix}_Prop_")
    metrics = diversity_metrics(grouped)

    result[f"{prefix}_Richness"] = metrics["Richness"]
    result[f"{prefix}_Shannon"] = metrics["Shannon"]

    # Fraction of the community with known classification data
    result[f"{prefix}_KnownFraction"] = (
        totals / counts.sum(axis=1).replace(0, np.nan)).fillna(0)

    return result



""" LOAD AND CLEAN DATA """

# Load datasets
seeds = pd.read_csv(DATA_DIR / "seeds.csv")
plots = pd.read_csv(DATA_DIR / "plots.csv")
species = pd.read_csv(DATA_DIR / "species.csv")

# Standardization and cleaning
seeds["Plot.ID"] = normalize_ids(seeds["Plot.ID"])
plots["Plot"] = normalize_ids(plots["Plot"])

seeds["Species"] = (seeds["Species"].astype("string").str.strip())
species["Species"] = (species["Species"].astype("string").str.strip())

seeds["Species"] = seeds["Species"].replace({
    "PTGA.YEL": "PTGA",
    "SOLANACEAE": "SOLAN.sp."})

seeds["Num.Seed"] = pd.to_numeric(seeds["Num.Seed"], errors="coerce")

# Prevent ambiguous merges caused by duplicate identifiers
if plots["Plot"].duplicated().any():
    raise ValueError("Duplicate plot IDs in plots.csv")

if species["Species"].duplicated().any():
    raise ValueError("Duplicate codes in species.csv")

matched_codes = set(species["Species"].dropna())
unmatched = sorted(set(seeds["Species"].dropna()) - matched_codes)


print("Matched observations:", len(seeds))
print("Matched species:", seeds["Species"].nunique())
print("Unmatched species codes:", len(unmatched))



""" COMMUNITY ABUNDANCE AND COMPOSITION """

# Count records for each species in each plot.
# Each row is treated as one individual for abundance calculations.
community = pd.crosstab(seeds["Plot.ID"], seeds["Species"]).astype(float)

if "VERO" not in community.columns:
    raise ValueError("VERO is missing from matched species.")

total = community.sum(axis=1)

relative = community.div(
    total.replace(0, np.nan),
    axis=0
).fillna(0)

predictors = pd.DataFrame(index=community.index)

# Separate VERO abundance from the abundance of other species
predictors["Community_Individuals"] = total
predictors["VERO_Individuals"] = community["VERO"]
predictors["Other_Individuals"] = (total - community["VERO"])
predictors["VERO_Proportion"] = relative["VERO"]

for code in relative.columns:
    if code != "VERO":
        predictors[f"SpeciesProp_{code}"] = relative[code]



""" SPECIES DIVERSITY """

alpha = diversity_metrics(community)

for metric in alpha.columns:
    predictors[f"Species_{metric}"] = alpha[metric]



""" BETA DIVERSITY """

# Bray-Curtis measures differences in community composition
# between plots based on species abundances.
if len(community) > 1:
    distances = squareform(
        pdist(community.values, metric="braycurtis"))

    np.fill_diagonal(distances, np.nan)

    predictors["Mean_BrayCurtis"] = np.nanmean(distances, axis=1)

else:
    predictors["Mean_BrayCurtis"] = 0.0



""" LIFE FORM AND FAMILY COMPOSITION """

# Group species by ecological life form and taxonomic family
# to capture community structure beyond individual species codes
life_form = attribute_composition(community, species, "life.form", "LifeForm")
family = attribute_composition(community, species, "family", "Family")

predictors = predictors.join(life_form)
predictors = predictors.join(family)



""" NATIVE AND EXOTIC COMPOSITION """

if "exotic" in species.columns:
    
    # Standardize different labels describing species origin
    origin = (
        species.set_index("Species")["exotic"]
        .astype("string")
        .str.strip()
        .str.lower())

    origin = origin.map({
        "yes": "Exotic",
        "y": "Exotic",
        "true": "Exotic",
        "1": "Exotic",
        "exotic": "Exotic",
        "introduced": "Exotic",
        "no": "Native",
        "n": "Native",
        "false": "Native",
        "0": "Native",
        "native": "Native"
    })

    origin = origin.reindex(community.columns)
    known_species = origin.dropna().index

    # Total individuals whose native/exotic status is known
    known_total = community[known_species].sum(axis=1)

    for category in ["Native", "Exotic"]:

        codes = origin.loc[origin == category].index
        subset = community.reindex(columns=codes, fill_value=0)

        # Calculate abundance, proportion, and richness by origin
        predictors[f"{category}_Individuals"] = (subset.sum(axis=1))

        predictors[f"{category}_Proportion"] = (
            subset.sum(axis=1)
            / known_total.replace(0, np.nan)).fillna(0)

        predictors[f"{category}_Richness"] = (
            (subset > 0).sum(axis=1))

    predictors["Origin_KnownFraction"] = (
        known_total / total.replace(0, np.nan)
    ).fillna(0)



""" COMMUNITY DOMINANCE """

# Sort species proportions from most to least abundant
sorted_props = np.sort(
    relative.to_numpy(), axis=1)[:, ::-1]

# Measure how strongly one or a few species dominate each plot
predictors["Dominant_Species_Proportion"] = (sorted_props[:, 0])

predictors["Top3_Species_Proportion"] = (sorted_props[:, :3].sum(axis=1))

predictors["Simpson_Concentration"] = ((relative ** 2).sum(axis=1))

predictors["Effective_Species_Number"] = (np.exp(alpha["Shannon"]))



""" NON-VERO COMPETITIVE CONTEXT """

# Exclude VERO to describe the surrounding plant community.
# These variables represent potential interspecific competition.
other = community.drop(columns=["VERO"])
other_metrics = diversity_metrics(other)

predictors["OtherSpecies_Richness"] = (other_metrics["Richness"])

predictors["OtherSpecies_Shannon"] = (other_metrics["Shannon"])

predictors["OtherSpecies_Simpson"] = (other_metrics["Simpson"])

predictors["OtherSpecies_Proportion"] = (
    other.sum(axis=1)
    / total.replace(0, np.nan)).fillna(0)



""" COMBINE WITH PLOT ENVIRONMENT """

# Convert plot-level predictors back into a regular dataframe
predictors.index.name = "Plot.ID"
predictors = predictors.reset_index()

plot_data = plots.rename(
    columns={"Plot": "Plot.ID"})

predictors = predictors.merge(
    plot_data,
    on="Plot.ID",
    how="left",
    validate="one_to_one")

# Keep only plots with usable VERO observations
vero = seeds.loc[
    (seeds["Species"] == "VERO")
    & seeds["Num.Seed"].notna()
    & (seeds["Num.Seed"] >= 0)
].copy()

vero = vero.loc[vero["Plot.ID"].isin(predictors["Plot.ID"])]

vero = vero.merge(
    predictors,
    on="Plot.ID",
    how="left",
    validate="many_to_one")

for column in environmental_features:
    vero[column] = pd.to_numeric(
        vero[column], errors="coerce")

# Remove observations missing required environmental measurements.
# High seed counts are retained; no outlier filtering is performed.
vero = vero.dropna(subset = environmental_features + ["Num.Seed"]).copy()


""" SUMMARY """

output_file = (DATA_DIR / "vero_ecological_predictors.csv")

vero.to_csv(output_file, index=False)

summary = pd.DataFrame({
    "Predictor": predictors.columns,
    "Missing_Values": predictors.isna().sum().values,
    "Unique_Values": predictors.nunique().values})

summary.to_csv(
    OUTPUT_DIR / "predictor_summary.csv",
    index=False)

print("VERO observations:", len(vero))
print("VERO plots:", vero["Plot.ID"].nunique())
print("Matched species:", community.shape[1])
print("Dataset columns:", len(vero.columns))
