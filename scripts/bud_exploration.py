"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python File: bud_exploration


General Bud Exploration:
    - Calculate the total number of buds per species
    - Calculate the total number of buds per plot
    - Create two bar charts for visualization
        1. Total bud count per species
        2. Total bud count per plot
"""


# Libraries
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt



""" PREPARE AND CALL DATA """

# Project paths
ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR_EX = ROOT / "figures" / "exploration"
FIGURE_DIR_EX.mkdir(parents=True, exist_ok=True)

# Load data
buds = pd.read_csv(PROCESSED_DATA_DIR / "buds.csv")
plots = pd.read_csv(PROCESSED_DATA_DIR / "plots.csv")

# Merge bud observations with plot data
df = buds.merge(
    plots,
    left_on="ID",
    right_on="Name",
    how="left",
    validate="many_to_one")



""" GENERAL BUD EXPLORATION """

# bud counts by species
species_counts = (
    buds.groupby("SP").agg(
    Plant_Count=("SP", "size"),
    Total_Buds=("buds", "sum"),
    Mean_Buds = ("buds", "mean"))).round(2)

print(f"\n{'-' * 50}\nPLANT AND BUD TOTALS PER SPECIES\n{'-' * 50}")
print(species_counts)


# Bud count per plot
bud_counts = (
    df.groupby("Plot").agg(
        Plant_Count=("SP", "size"),
        Total_Buds=("buds", "sum"),
        Mean_Buds=("buds", "mean")
    )
).round(2)

print(f"\n{'-' * 50}\nBUD COUNT PER PLOT\n{'-' * 50}")
print(bud_counts)



""" PLOTTING """

# Plot total buds per species
plt.barh(
    species_counts.index,
    species_counts["Total_Buds"],
    color = "brown")

plt.xlabel("Total Buds")
plt.ylabel("Species")
plt.title("Total Bud Count per Species")

plt.tight_layout()


plt.savefig(
    FIGURE_DIR_EX / "buds_per_species.png",
    dpi=300,
    bbox_inches="tight")

plt.show()


# Plot total buds per plot
plt.figure(figsize=(12, 6))

plt.bar(
    bud_counts.index,
    bud_counts["Total_Buds"],
    color = "salmon")

plt.xticks(range(0, 100, 10))
plt.xlim(0, 100)
plt.xlabel("Plot")
plt.ylabel("Total Buds")
plt.title("Total Bud Count per Plot")

plt.tight_layout()


# Save figure
plt.savefig(
    FIGURE_DIR_EX / "buds_per_plot.png",
    dpi=300,
    bbox_inches="tight")

plt.show()
