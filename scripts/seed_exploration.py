"""
Author: Kaitlyn Hill
Faculty Advisor: Dr. Trace Martyn
Lab: Martyn Ecology at Oregon State University
Python file: seed_exploration


General Seed Exploration:
    - Summarize species observations and seed production
    - Calculate total, mean, median, standard deviation, minimum,
      and maximum seed counts by species
    - Examine species observations across plots
    - Visualize:
        1. Total seed production per species
        2. Total seed production per plot
        3. Plant observations per plot

Target Species Exploration:
    - Explore VERO, ARCA, PEAI, and POCA in greater detail
    - Summarize observations, total seeds, mean seeds, and median seeds
      by species and plot
    - Visualize:
        1. Species observations per plot
        2. Species seed production per plot
    - Identify potential outliers using the IQR method
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
FIGURE_DIR_3 = ROOT / "figures" / "model_3"
FIGURE_DIR_EX.mkdir(parents=True, exist_ok=True)
FIGURE_DIR_3.mkdir(parents=True, exist_ok=True)

# Load Data
seeds = pd.read_csv(PROCESSED_DATA_DIR / "seeds.csv")



""" GENERAL SEED EXPLORATION """

# Overall seed production summary
seed_summary = (
    seeds["Num.Seed"]
    .agg(
        Mean="mean",
        Standard_Deviation="std",
        Minimum="min",
        Percentile_25=lambda x: x.quantile(0.25),
        Median="median",
        Percentile_75=lambda x: x.quantile(0.75),
        Maximum="max")
    .round(2))


print(f"\n{'-' * 50}\nSEED PRODUCTION SUMMARY\n{'-' * 50}")
print(seed_summary)


# Species summary
species_summary = (
    seeds.groupby("Species").agg(
    Observations =("Species", "size"),
    Total_seeds=("Num.Seed", "sum"),
    Mean_seeds = ("Num.Seed", "mean"),
    Median_seeds = ("Num.Seed", "median"),
    std = ("Num.Seed", "std"),
    min_seeds = ("Num.Seed", "min"),
    max_seeds = ("Num.Seed", "max")
    )
    .round(2)
    .sort_values("Total_seeds", ascending = False))


print(f"\n{'-' * 50}\nSPECIES SUMMARY\n{'-' * 50}")
print(species_summary)


# Species observations per plot
species_counts_plot = (
    seeds.pivot_table(
        index="Plot.ID",
        columns="Species",
        values="Num.Seed",
        aggfunc="size",
        fill_value=0))

# Seeds per species
seeds_per_species = (
    seeds.groupby("Species")["Num.Seed"]
    .sum()
    .sort_values(ascending=False))

# Seeds per plot
seeds_per_plot = (
    seeds.groupby("Plot.ID")["Num.Seed"]
    .sum())


# Total plant observations per plot
plot_counts = (
    seeds.groupby("Plot.ID")
      .size()
      .rename("plant_observations"))

# Move plant_observations column to the front
species_counts = species_counts_plot.join(plot_counts)

species_counts = species_counts[
    ["plant_observations"]
    + [column for column in species_counts.columns
       if column != "plant_observations"]]

print(f"\n{'-' * 50}\nSPECIES OBSERVATION PER PLOT\n{'-' * 50}")
print(species_counts)



""" PLOTTING """

# Total seeds per species
plt.figure(figsize=(16, 6))

plt.bar(
    seeds_per_species.index,
    seeds_per_species.values,
    color = "red")

plt.xlabel("Species")
plt.ylabel("Total Number of Seeds")
plt.title("Total Seed Production per Species")

plt.xticks(rotation=90)
plt.tight_layout()

plt.savefig(
    FIGURE_DIR_EX / "seeds_per_species.png",
    dpi=300,
    bbox_inches="tight")

plt.show()


# Total seeds per plot
plt.figure(figsize=(16, 6))

plt.bar(
    seeds_per_plot.index,
    seeds_per_plot.values)

plt.xlabel("Plot")
plt.ylabel("Total Number of Seeds")
plt.title("Total Seed Production per Plot")

plt.xlim(0, 100)
plt.tight_layout()

plt.savefig(
    FIGURE_DIR_EX / "seeds_per_plot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# Total plant observations per plot
plt.figure(figsize=(16, 6))

plt.bar(
    plot_counts.index,
    plot_counts.values,
    color = "seagreen")

plt.xlabel("Plot")
plt.ylabel("Number of Plant Observations")
plt.title("Plant Observations per Plot")

plt.xlim(0, 100)
plt.tight_layout()

plt.savefig(
    FIGURE_DIR_EX / "plant_observations_per_plot.png",
    dpi=300,
    bbox_inches="tight")

plt.show()




""" TARGET SEED EXPLORATION """


top_species = ["VERO", "ARCA", "PEAI", "POCA"]
seeds_top = seeds[seeds["Species"].isin(top_species)].copy()


# Summarize species seed data
species_top_summary = (
    seeds_top
    .groupby(["Plot.ID", "Species"])
    .agg(
        Entries=("Num.Seed", "size"),
        Total_Seeds=("Num.Seed", "sum"),
        Mean_Seeds=("Num.Seed", "mean"),
        Median_Seeds=("Num.Seed", "median"))
    .reset_index()
    .round({
        "Mean_Seeds": 2,
        "Median_Seeds": 2}))

print(f"\n{'-' * 50}\nTARGET SPECIES SUMMARY\n{'-' * 50}")
print(species_top_summary)


""" PLOTTING """

# Number of species observations per plot barchart
for species in top_species:

    data = species_top_summary[
        species_top_summary["Species"] == species]

    plt.figure(figsize=(16, 6))

    plt.bar(
        data["Plot.ID"],
        data["Entries"],
        color = "mediumvioletred")

    plt.xlim(0,100)
    plt.xlabel("Plot")
    plt.ylabel("Number of Entries")
    plt.title(f"Number of {species} Observations per Plot")
    plt.tight_layout()
    
    plt.savefig(
        FIGURE_DIR_3 / f"{species}_observations_per_plot.png",
        dpi=300,
        bbox_inches="tight")
    
    plt.show()


# Sum of species seed production per plot barchart
for species in top_species:

    data = species_top_summary[
        species_top_summary["Species"] == species]

    plt.figure(figsize=(16, 6))

    plt.bar(
        data["Plot.ID"],
        data["Total_Seeds"],
        color = "pink")

    plt.xlim(0,100)
    plt.xlabel("Plot")
    plt.ylabel("Total Number of Seeds")
    plt.title(f"Total {species} Seed Production per Plot")
    plt.tight_layout()
    
    plt.savefig(
        FIGURE_DIR_3 / f"{species}_seeds_per_plot.png",
        dpi=300,
        bbox_inches="tight")
    
    plt.show()



""" OUTLIERS """

# Results determined in RESEARCH_LOG.md
outliers = []

for species in top_species:

    data = species_top_summary[species_top_summary["Species"] == species]

    Q1 = data["Total_Seeds"].quantile(0.25)
    Q3 = data["Total_Seeds"].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    species_outliers = data[
        (data["Total_Seeds"] < lower_bound) |
        (data["Total_Seeds"] > upper_bound)].copy()

    outliers.append(species_outliers)
outliers = pd.concat(outliers)


print(f"\n{'-' * 50}\nOUTLIERS\n{'-' * 50}")
print(outliers)

