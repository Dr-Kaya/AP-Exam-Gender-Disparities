"""
analyze_trends.py
=================
Command-line script for reproducing the Mann–Kendall trend analysis and
Sen's slope estimation reported in:

    "Mapping Gender Disparities in Advanced Academics: Participation and
     Top Achievement Trends Across Advanced Placement (AP) Exams"

Usage
-----
    python analyze_trends.py tapar.csv
    python analyze_trends.py tapar.csv --output results.csv

The script reads the AP gender disparity dataset, runs the Mann–Kendall
test and Sen's slope estimator for each of the 45 AP exam subjects, prints
a summary to the console, and (optionally) saves results to CSV/Excel.

Dependencies
------------
    pip install pandas numpy pymannkendall scipy openpyxl

Author: [Masked for review]
License: MIT
"""

import argparse
import sys

import numpy as np
import pandas as pd
import pymannkendall as mk
from scipy import stats


# ---------------------------------------------------------------------------
# Data Loading and Preparation
# ---------------------------------------------------------------------------

def load_and_prepare(csv_path: str) -> pd.DataFrame:
    """
    Load the AP gender disparity CSV and prepare it for analysis.

    The raw CSV is stored with exam subjects as rows and years as columns.
    This function transposes the data so that each row represents a year
    and each column an exam subject, making it compatible with time-series
    analysis functions.

    Parameters
    ----------
    csv_path : str
        Path to the input CSV file (e.g., 'tapar.csv').

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with a 'Year' column and one column per AP exam.
        All values are cast to numeric. The final row (a summary average
        row present in the raw data) is dropped before analysis.
    """
    # Step 1: Load the raw CSV
    df_raw = pd.read_csv(csv_path)

    # Step 2: Transpose so rows = years, columns = exam subjects
    df_transposed = df_raw.T
    header = df_transposed.iloc[0]          # First row after transpose = subject names
    df_transposed = df_transposed.iloc[1:]  # Drop the header row from data
    df_transposed.columns = header
    df_transposed.reset_index(inplace=True)
    df_transposed.rename(columns={'index': 'Year'}, inplace=True)

    # Step 3: Keep only the 46 relevant columns (Year + 45 AP exam subjects)
    df_transposed = df_transposed[df_transposed.columns[:46]]

    # Step 4: Drop the last row (a pre-computed average row in the raw data)
    df_transposed.drop(index=df_transposed.index[-1], inplace=True)

    # Step 5: Convert all columns to numeric (Year and MFR values)
    df_clean = df_transposed.apply(pd.to_numeric, errors='coerce')

    return df_clean


# ---------------------------------------------------------------------------
# Individual Exam Analysis
# ---------------------------------------------------------------------------

def analyze_exam(series: pd.Series, years: pd.Series) -> dict:
    """
    Run the Mann–Kendall test and compute descriptive statistics for one
    AP exam's gender disparity time series.

    The Mann–Kendall (MK) test is a non-parametric test for monotonic
    trends in time-series data. It makes no assumption about the
    distribution of the data and is robust to outliers and missing values.
    Sen's slope provides a robust estimate of the rate of change per year.

    Parameters
    ----------
    series : pd.Series
        MFR index values for one AP exam across all years.
    years : pd.Series
        Corresponding year values (used to compute a meaningful intercept).

    Returns
    -------
    dict
        Dictionary containing:
        - trend      : 'increasing', 'decreasing', or 'no trend'
        - p          : p-value of the MK test (two-tailed)
        - slope      : Sen's slope (MFR units per year)
        - z          : Standardized MK test statistic
        - Tau        : Kendall's Tau correlation coefficient
        - s          : MK S statistic (sum of sign differences)
        - var_s      : Variance of S
        - intercept  : Estimated intercept (value at Year = 0 using Sen's slope)
        - minimum    : Minimum non-zero MFR value in the series
        - maximum    : Maximum non-zero MFR value in the series
        - mean       : Mean MFR value
        - std_dev    : Standard deviation of MFR values
        - n_obs      : Number of valid observations
    """
    # Run the Mann–Kendall original test
    result = mk.original_test(series)

    # Compute intercept: back-calculate from the last known data point
    # so the trend line is anchored to observed data
    intercept = series.iloc[-1] - result.slope * years.iloc[-1]

    # Descriptive statistics (excluding zeros, which represent missing data)
    series_nonzero = series.mask(series == 0)
    minimum = series_nonzero.min()
    maximum = series_nonzero.max()

    return {
        'trend':     result.trend,
        'p':         round(result.p, 4),
        'slope':     round(result.slope, 4),
        'z':         round(result.z, 4),
        'Tau':       round(result.Tau, 4),
        's':         result.s,
        'var_s':     round(result.var_s, 4),
        'intercept': round(intercept, 4),
        'minimum':   round(minimum, 4) if pd.notna(minimum) else None,
        'maximum':   round(maximum, 4) if pd.notna(maximum) else None,
        'mean':      round(series.mean(), 4),
        'std_dev':   round(series.std(), 4),
        'n_obs':     int(series.count()),
    }


# ---------------------------------------------------------------------------
# Main Analysis Loop
# ---------------------------------------------------------------------------

def run_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run Mann–Kendall analysis across all 45 AP exam subjects.

    Iterates over all exam columns (i.e., all columns except 'Year'),
    calls analyze_exam() for each, and collects results into a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared DataFrame with 'Year' column and one column per exam.

    Returns
    -------
    pd.DataFrame
        Results table with one row per AP exam and columns for all
        Mann–Kendall statistics and descriptive measures.
    """
    years = df['Year']
    results = []

    exam_columns = df.columns[1:]  # Skip the 'Year' column

    for col in exam_columns:
        print(f"  Analyzing: {col} ...", flush=True)
        stats_dict = analyze_exam(df[col], years)
        stats_dict['exam'] = col
        results.append(stats_dict)

    # Build results DataFrame with a logical column order
    results_df = pd.DataFrame(results)
    column_order = [
        'exam', 'trend', 'p', 'slope', 'z', 'Tau', 's', 'var_s',
        'intercept', 'minimum', 'maximum', 'mean', 'std_dev', 'n_obs'
    ]
    return results_df[column_order]


def print_results(results_df: pd.DataFrame) -> None:
    """
    Print a human-readable summary of results to the console.

    Parameters
    ----------
    results_df : pd.DataFrame
        Output from run_analysis().
    """
    separator = "-" * 60
    print("\n" + "=" * 60)
    print("  MANN–KENDALL TREND ANALYSIS RESULTS")
    print("  AP Exam Gender Disparity (MFR Index), 1997–2020")
    print("=" * 60)

    for _, row in results_df.iterrows():
        print(f"\nExam:          {row['exam']}")
        print(f"Trend:         {row['trend']}")
        print(f"p-value:       {row['p']}")
        print(f"Sen's Slope:   {row['slope']}  (MFR units/year)")
        print(f"Z-score:       {row['z']}")
        print(f"Tau:           {row['Tau']}")
        print(f"S statistic:   {row['s']}")
        print(f"Var(S):        {row['var_s']}")
        print(f"Intercept:     {row['intercept']}")
        print(f"Min (non-0):   {row['minimum']}")
        print(f"Max (non-0):   {row['maximum']}")
        print(f"Mean:          {row['mean']}")
        print(f"Std Dev:       {row['std_dev']}")
        print(f"N obs:         {row['n_obs']}")
        print(separator)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Mann–Kendall trend analysis and Sen's slope for AP exam "
            "gender disparity data (MFR-P and MFR-TA indices)."
        )
    )
    parser.add_argument(
        'csv_path',
        help="Path to the input CSV file (e.g., 'tapar.csv')"
    )
    parser.add_argument(
        '--output',
        default=None,
        help=(
            "Optional: path prefix for saving results. "
            "Creates <prefix>.csv and <prefix>.xlsx "
            "(e.g., --output results → results.csv + results.xlsx)"
        )
    )
    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Step 1: Load and prepare data
    # -----------------------------------------------------------------------
    print(f"\nLoading data from: {args.csv_path}")
    try:
        df = load_and_prepare(args.csv_path)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Data loaded: {df.shape[0]} years × {df.shape[1] - 1} AP exams")
    print(f"Year range:  {int(df['Year'].min())} – {int(df['Year'].max())}")

    # -----------------------------------------------------------------------
    # Step 2: Run Mann–Kendall analysis for all exams
    # -----------------------------------------------------------------------
    print("\nRunning Mann–Kendall tests...")
    results_df = run_analysis(df)

    # -----------------------------------------------------------------------
    # Step 3: Print results to console
    # -----------------------------------------------------------------------
    print_results(results_df)

    # -----------------------------------------------------------------------
    # Step 4: Optionally save results to CSV and Excel
    # -----------------------------------------------------------------------
    if args.output:
        csv_out = f"{args.output}.csv"
        xlsx_out = f"{args.output}.xlsx"
        results_df.to_csv(csv_out, index=False)
        results_df.to_excel(xlsx_out, index=False)
        print(f"\nResults saved to:\n  {csv_out}\n  {xlsx_out}")

    print("\nAnalysis complete.")


if __name__ == '__main__':
    main()
