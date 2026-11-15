
# Australian Plant Reproductive Output — Machine Learning Analysis

## Project Overview

This project investigates whether environmental conditions and ecological characteristics can be used to predict plant reproductive output using machine-learning methods.

The analysis uses ecological datasets collected for dissertation research by Dr. Trace Martyn at Oregon State University. Building on these existing datasets, the project explores how environmental variation, species identity, plant community composition, and functional diversity contribute to predictions of plant seed production.

The research progressed through six modeling stages (Models 0–5), beginning with broad predictions of reproductive output and ultimately focusing on individual seed production for *Velleia rosea* (VERO), now known as *Goodenia rosea*. Throughout this project, the species is referred to as **VERO** to maintain consistency with the original dataset.

For detailed documentation of the analyses, methods, results, and interpretations, see [RESEARCH_LOG.md](RESEARCH_LOG.md).

## Research Objectives

The project investigated three primary questions:

1. Can environmental conditions and species characteristics predict individual plant reproductive output?
2. Do additional ecological predictors, particularly plant diversity and functional composition, improve predictions of seed production?
3. How do different machine-learning and regression approaches compare when using the same environmental and ecological predictors?

## Data

The project uses four datasets containing information about individual plants, environmental conditions, seed production, and species characteristics.

The primary seed-production dataset contains **13,485 observations across 100 plots**, representing 70 plant species.

Later analyses focused on **VERO**, which was represented by 3,027 observations across 46 plots.

The datasets provide information on:

- Individual bud and seed production
- Plot-level environmental conditions, including soil water, soil phosphorus, vegetation cover, and canopy cover
- Species identity and taxonomic classification
- Plant functional groups and ecological community composition

## Methodology

The analysis was developed iteratively across six modeling stages.

| Model | Focus |
|---|---|
| Model 0 | Predicting bud production using environmental conditions |
| Model 1 | Predicting seed production using environmental conditions and species identity |
| Model 2 | Evaluating taxonomic family groupings as an alternative to individual species identity |
| Model 3 | Developing separate seed-production models for four well-represented species |
| Model 4 | Exploring additional ecological predictors, extreme seed counts, and cross-validation strategies for VERO |
| Model 5 | Comparing seven regression approaches using a selected set of environmental and functional ecological predictors |

The final analysis compared Random Forest, Poisson-criterion Random Forest, Negative Binomial Regression, Linear Regression, Gradient Boosting, Extra Trees, and K-Nearest Neighbors.

Model performance was evaluated using cross-validation and three metrics: R², mean absolute error (MAE), and root mean squared error (RMSE). Feature importance was also examined to identify predictors contributing to model performance.

## Key Findings

- **Environmental predictors alone provided limited predictive accuracy**, particularly when evaluating models on previously unseen plots.
- **Plant functional diversity and composition contributed useful predictive information** when incorporated alongside environmental conditions.
- **Gradient Boosting achieved the highest performance** in the final comparison, with a mean R² of 0.203, MAE of 10.83 seeds, and RMSE of 17.87 seeds.
- **Tree-based ensemble methods performed similarly**, suggesting that changing algorithms alone offered limited improvements.
- **Soil water and plant functional diversity** were consistently among the most influential predictors in the leading models.

Despite these findings, much of the variation in individual seed production remained unexplained.

The final models used standard KFold cross-validation, which evaluates held-out observations within the sampled plot population rather than generalization to entirely unseen plots. Predictor selection was also conducted using the same dataset, so reported performance may be optimistic.

Overall, the results suggest that identifying additional informative ecological predictors may be more valuable than changing the modeling algorithm alone.

## Repository Structure

The repository is organized into the following main components:

- **`data/`** — Cleaned datasets used throughout the analyses
- **`scripts/`** — Python scripts for data exploration, feature engineering, and machine-learning models
- **`figures/`** — Visualizations of exploratory analyses, model performance, and feature importance
- **`RESEARCH_LOG.md`** — Detailed documentation of the research process, methodology, results, and interpretations

## Research Context

This project was conducted as undergraduate research at **Oregon State University**, under the supervision of **Dr. Trace Martyn**, using ecological datasets from her dissertation research.
