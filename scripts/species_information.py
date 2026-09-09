"""
Author: Kaitlyn Hill
Lab: Martyn Ecology at Oregon State University
Python File: species_information

Purpose:
    Identify all species within the seeds.csv file with the information from the
    species.csv file. All entries made in the species.csv without a match are
    disregarded.

    Missing information will be added
"""

# Libraries
from pathlib import Path
import pandas as pd


""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_R = ROOT / "data" / "raw"
PROCESSED_DATA_DIR = ROOT / "data" / "processed"


# Load data
seeds = pd.read_csv(PROCESSED_DATA_DIR / "seeds.csv")
species = pd.read_csv(PROCESSED_DATA_R / "species_data.csv")



""" FIND MISSING VALUES """

# Get unique species from seeds.csv
seed_species = (
    seeds[["Species"]]
    .drop_duplicates()
    .sort_values("Species")
    .reset_index(drop=True))

print(f"\n{'-' * 50}\nUNIQUE SPECIES IN SEEDS.CSV\n{'-' * 50}")
print(seed_species)


# Merge files
species_match = seed_species.merge(
    species,
    left_on="Species",
    right_on="code",
    how="left",
    validate="one_to_one",
    indicator=True)


# Matches species
matched_species = (
    species_match[
        species_match["_merge"] == "both"]
    .drop(columns="_merge")
    .reset_index(drop=True))

print(f"\n{'-' * 50}\nMATCHED SPECIES\n{'-' * 50}")
print(matched_species)


# Unmatches species
unmatched_species = (
    species_match.loc[
        species_match["_merge"] == "left_only",
        "Species"]
    .reset_index(drop=True))

print(f"\n{'-' * 50}\nUNMATCHED SPECIES FROM SEEDS.CSV\n{'-' * 50}")
print(unmatched_species)


# Summary
print(f"\n{'-' * 50}\nMATCH SUMMARY\n{'-' * 50}")
print(f"Unique species in seeds.csv: {len(seed_species)}")
print(f"Matched species: {len(matched_species)}")
print(f"Unmatched species: {len(unmatched_species)}")



""" CREATE NEW CSV """
# Keep relevent data and add all missing data

