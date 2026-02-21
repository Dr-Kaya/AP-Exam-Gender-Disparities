# Gender Disparities in Advanced Placement (AP) Exams: Trend Analysis

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Dr-Kaya/TrendAnalysis/blob/main/AP_Gender_Trend_Analysis.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

This repository contains the data and analysis code for the paper:

> **"Mapping Gender Disparities in Advanced Academics: Participation and Top Achievement Trends Across Advanced Placement (AP) Exams"**

The study uses **non-parametric trend analysis** — specifically the **Mann–Kendall (MK) test** and **Sen's slope estimator** — to examine longitudinal changes in gender disparities across 45 AP exam subjects from **1997 to 2020**. Two gender disparity indices are analyzed:

- **MFR-P** — Male-to-Female Ratio in *Participation*
- **MFR-TA** — Male-to-Female Ratio in *Top Achievement* (students scoring 5)

A Spearman's rank correlation analysis examines the relationship between MFR-P and MFR-TA across subjects.

---

## Repository Structure

```
TrendAnalysis/
├── AP_Gender_Trend_Analysis.ipynb   # Main analysis notebook (run in Colab or Jupyter)
├── analyze_trends.py                # Command-line script for reproducible batch analysis
├── tapar.csv                        # AP participation data (MFR-P and MFR-TA by subject/year)
├── requirements.txt                 # Python package dependencies
└── README.md                        # This file
```

---

## Quick Start: Run in Google Colab (No Installation Required)

Click the badge below to open the notebook directly in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Dr-Kaya/TrendAnalysis/blob/main/AP_Gender_Trend_Analysis.ipynb)

The notebook installs all dependencies automatically, loads the data directly from this GitHub repository, and walks through the full analysis step by step.

---

## Local Installation

### Requirements

- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/Dr-Kaya/TrendAnalysis.git
cd TrendAnalysis

# Install dependencies
pip install -r requirements.txt
```

### Run the Notebook

```bash
jupyter notebook AP_Gender_Trend_Analysis.ipynb
```

### Run the Command-Line Script

```bash
python analyze_trends.py tapar.csv
```

This prints Mann–Kendall statistics and Sen's slope for each of the 45 AP exam subjects.

---

## Data Description

The dataset (`tapar.csv`) contains longitudinally structured data compiled from publicly available College Board AP reports spanning **1997–2020**. The file is organized with AP exam subjects as columns and years as rows. Each cell contains the computed disparity index (MFR-P or MFR-TA) for that subject in that year.

| Field | Description |
|---|---|
| Year | Academic year (1997–2020) |
| [Exam Name] | MFR index value for that exam and year |

> **Note:** An MFR value > 1.0 indicates male overrepresentation; a value < 1.0 indicates female overrepresentation; a value of 1.0 indicates parity.

---

## Analysis Methods

| Method | Purpose | Python Package |
|---|---|---|
| Mann–Kendall Test | Detect presence and direction of monotonic trend | `pymannkendall` |
| Sen's Slope | Estimate magnitude of trend (units per year) | `pymannkendall` |
| Spearman's Correlation | Examine relationship between MFR-P and MFR-TA | `scipy.stats` |

All tests are two-tailed. Given the large number of subject-specific analyses, findings were interpreted with attention to both statistical significance (p < .05) and effect magnitude (Sen's slope).

---

## Dependencies

```
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
seaborn>=0.11.0
pymannkendall>=1.4.2
scipy>=1.7.0
openpyxl>=3.0.0
```

Install all at once: `pip install -r requirements.txt`

---

## Citation

If you use this code or data in your research, please cite:

```
[Authors masked for review]. (in press). Mapping Gender Disparities in Advanced Academics:
Participation and Top Achievement Trends Across Advanced Placement (AP) Exams.
```

---

## Transparency and Openness

This project follows the **Transparency and Openness Promotion (TOP) Guidelines**. All data, analysis code, and research materials are publicly available in this repository. The study design and analysis were not pre-registered.

Data were analyzed using **Python 3** with the following key packages:
- `pymannkendall` v1.4.2 (for Mann–Kendall tests and Sen's slope)
- `scipy` (for Spearman's rank correlation)
- `pandas` and `numpy` (for data wrangling)
- `matplotlib` and `seaborn` (for visualization)

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contact

For questions about the code or analysis, please open an [Issue](https://github.com/Dr-Kaya/TrendAnalysis/issues) in this repository.
