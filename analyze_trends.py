"""
analyze_trends.py
=================
Command-line script for reproducing the Mann-Kendall trend analysis and
Sen's slope estimation reported in:

    "Mapping Gender Disparities in Advanced Academics: Participation and
     Top Achievement Trends Across Advanced Placement (AP) Exams"

This script replicates the exact pipeline from AP_Gender_Trend_Analysis.ipynb.
Run against both data files to reproduce Tables 3, 4, and 5:

    # Reproduces Table 3 (RQ1 - participation trends)
    python analyze_trends.py participation.csv --output participation_results

    # Reproduces Table 4 (RQ2 - top achievement trends)
    python analyze_trends.py top_achievement.csv --output top_achievement_results

    # Reproduces both + Spearman correlation Table 5 (RQ3)
    python analyze_trends.py participation.csv top_achievement.csv --output results

Dependencies
------------
    pip install pandas numpy pymannkendall scipy openpyxl

Repository
----------
    https://github.com/Dr-Kaya/AP-Exam-Gender-Disparities

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

def load_and_prepare(csv_path):
    """
    Load an AP gender disparity CSV and prepare it for Mann-Kendall analysis.

    The raw CSV stores AP exam subjects as rows and years as columns.
    This function:
      1. Loads the CSV
      2. Transposes so rows = years, columns = exam subjects
      3. Drops the 'Average' summary column (not a real year)
      4. Drops any NaN-named columns (from empty rows in the raw file)
      5. Drops the last row (a pre-computed average row, not a real year)
      6. Converts all values to numeric

    Parameters
    ----------
    csv_path : str
        Path to input CSV ('participation.csv' or 'top_achievement.csv').

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame: rows = years (1997-2020), columns = Year + AP exams.
    """
    # Step 1: Load
    df_raw = pd.read_csv(csv_path)

    # Step 2: Transpose - exam subjects become columns, years become rows
    df2 = df_raw.T
    header = df2.iloc[0]        # First row after transpose = exam subject names
    df2 = df2[1:]               # Remove header row from data
    df2.columns = header
    df2.reset_index(inplace=True)
    df2.rename(columns={'index': 'Year'}, inplace=True)

    # Step 3: Drop 'Average' summary column
    if 'Average' in df2.columns:
        df2 = df2.drop(columns=['Average'])

    # Step 4: Drop NaN-named columns (empty rows become NaN column names after transpose)
    df2 = df2.loc[:, df2.columns.notna()]

    # Step 5: Drop last row (pre-computed average row, not a real year)
    df2.drop(index=df2.index[-1], inplace=True)

    # Step 6: Convert all to numeric
    df3 = df2.apply(pd.to_numeric, errors='coerce')

    return df3


# ---------------------------------------------------------------------------
# Individual Exam Analysis
# ---------------------------------------------------------------------------

def analyze_exam(series):
    """
    Run the Mann-Kendall test and compute Sen's slope for one AP exam series.

    The Mann-Kendall test is a non-parametric rank-based test for monotonic
    trends. It makes no distributional assumptions and is robust to outliers
    and missing values -- well-suited for longitudinal educational data.

    Sen's slope is the median of all pairwise slopes and provides a robust
    estimate of the rate of change per year.

    NaN values are dropped before testing. Zeros are excluded from min/max
    statistics as they represent missing/unreported data. A minimum of 3
    valid observations is required (fewer causes ZeroDivisionError in the
    Tau calculation).

    Parameters
    ----------
    series : pd.Series
        MFR index values for one AP exam across years.

    Returns
    -------
    dict
        Mann-Kendall statistics and descriptive measures.
    """
    clean = series.dropna()

    # Require at least 3 observations -- Tau = s / (0.5 * n * (n-1)) divides by zero for n < 2
    if len(clean) < 3:
        return {
            'Trend': 'insufficient data', 'p': None, 'slope': None,
            'z': None, 'intercept': None, 'Tau': None, 's': None,
            'var_s': None, 'minimum': None, 'maximum': None,
            'mean': round(float(clean.mean()), 4) if len(clean) > 0 else None,
            'SD': None, 'n': int(len(clean)),
        }

    # Run Mann-Kendall original test
    trend, h, p, z, Tau, s, var_s, slope, intercept = mk.original_test(clean)

    # Exclude zeros when computing min/max (zeros = missing data in this dataset)
    nonzero = series.mask(series == 0)

    return {
        'Trend':     trend,
        'p':         round(p, 4),
        'slope':     round(slope, 4),
        'z':         round(z, 4),
        'intercept': round(intercept, 4),
        'Tau':       round(Tau, 4),
        's':         int(s),
        'var_s':     round(var_s, 4),
        'minimum':   round(float(nonzero.min()), 4),
        'maximum':   round(float(nonzero.max()), 4),
        'mean':      round(float(series.mean()), 4),
        'SD':        round(float(series.std(ddof=1)), 4),
        'n':         int(clean.count()),
    }


# ---------------------------------------------------------------------------
# Full Dataset Analysis
# ---------------------------------------------------------------------------

def run_analysis(df, label):
    """
    Run Mann-Kendall analysis across all AP exam columns in a dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared DataFrame from load_and_prepare().
    label : str
        Display label for output (e.g., 'MFR-P').

    Returns
    -------
    pd.DataFrame
        One row per AP exam with all Mann-Kendall statistics.
    """
    rows = []
    for col in df.columns[1:]:      # Skip 'Year'
        result = analyze_exam(df[col])
        result['Exam'] = col
        rows.append(result)

    results_df = pd.DataFrame(rows)
    col_order = ['Exam', 'Trend', 'p', 'slope', 'z', 'intercept',
                 'Tau', 's', 'var_s', 'minimum', 'maximum', 'mean', 'SD', 'n']
    results_df = results_df[col_order].reset_index(drop=True)

    sig = (results_df['p'] < 0.05).sum()
    print(f"  [{label}] {len(results_df)} exams | Significant (p < .05): {sig}/{len(results_df)}")
    return results_df


# ---------------------------------------------------------------------------
# Spearman Correlation (RQ3)
# ---------------------------------------------------------------------------

def run_spearman(df_par, df_ta):
    """
    Compute Spearman rank correlation between MFR-P and MFR-TA for each exam.

    Spearman's rho is used because it makes no linearity assumption and is
    robust to outliers -- appropriate for MFR index values.

    Parameters
    ----------
    df_par : pd.DataFrame   Prepared MFR-P dataset (participation).
    df_ta  : pd.DataFrame   Prepared MFR-TA dataset (top achievement).

    Returns
    -------
    pd.DataFrame
        Spearman rho, p-value, significance flag, and n for each AP exam.
    """
    rows = []
    for col in df_par.columns[1:]:
        combined = pd.DataFrame({
            'MFR_P':  df_par[col].values,
            'MFR_TA': df_ta[col].values if col in df_ta.columns else np.nan
        }).dropna()

        if len(combined) >= 4:
            rho, p_val = stats.spearmanr(combined['MFR_P'], combined['MFR_TA'])
        else:
            rho, p_val = np.nan, np.nan

        rows.append({
            'Exam':        col,
            'rho':         round(rho, 3) if not np.isnan(rho) else None,
            'p-value':     round(p_val, 3) if not np.isnan(p_val) else None,
            'Significant': bool(p_val < 0.05) if not np.isnan(p_val) else None,
            'n':           len(combined),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Results Printing
# ---------------------------------------------------------------------------

def print_results(results_df, label):
    """Print a formatted Mann-Kendall results summary to the console."""
    sep = "-" * 65
    print(f"\n{'=' * 65}")
    print(f"  MANN-KENDALL RESULTS -- {label}")
    print(f"  AP Exam Gender Disparity (1997-2020)")
    print(f"{'=' * 65}")

    for _, row in results_df.iterrows():
        if row['Trend'] == 'insufficient data':
            print(f"\n{row['Exam']}: insufficient data (n={row['n']})")
            continue
        print(f"\nExam:        {row['Exam']}")
        print(f"Trend:       {row['Trend']}")
        print(f"p-value:     {row['p']}")
        print(f"Sen's Slope: {row['slope']}  (MFR units/year)")
        print(f"Z-score:     {row['z']}")
        print(f"Tau:         {row['Tau']}")
        print(f"S:           {row['s']}")
        print(f"Var(S):      {row['var_s']}")
        print(f"Min:         {row['minimum']}")
        print(f"Max:         {row['maximum']}")
        print(f"Mean:        {row['mean']}")
        print(f"SD:          {row['SD']}")
        print(f"N obs:       {row['n']}")
        print(sep)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Mann-Kendall trend analysis for AP exam gender disparity data.\n\n"
            "Provide one file for MK analysis only, or both files to also\n"
            "compute Spearman correlations between MFR-P and MFR-TA.\n\n"
            "Examples:\n"
            "  python analyze_trends.py participation.csv\n"
            "  python analyze_trends.py top_achievement.csv\n"
            "  python analyze_trends.py participation.csv top_achievement.csv --output results"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'csv_files', nargs='+',
        help="One or two CSV files: participation.csv and/or top_achievement.csv"
    )
    parser.add_argument(
        '--output', default=None,
        help="Prefix for output files (e.g., --output results)"
    )
    args = parser.parse_args()

    all_results = {}

    # Run Mann-Kendall for each provided file
    for csv_path in args.csv_files:
        if 'participation' in csv_path.lower():
            label = 'MFR-P (Participation)'
            suffix = 'participation'
        elif 'achievement' in csv_path.lower():
            label = 'MFR-TA (Top Achievement)'
            suffix = 'top_achievement'
        else:
            label = csv_path
            suffix = csv_path.replace('.csv', '')

        print(f"\nLoading: {csv_path}")
        try:
            df = load_and_prepare(csv_path)
        except FileNotFoundError:
            print(f"ERROR: File not found: {csv_path}", file=sys.stderr)
            sys.exit(1)

        print(f"  {df.shape[0]} years x {df.shape[1]-1} exams  |  "
              f"Years: {int(df['Year'].min())}-{int(df['Year'].max())}")

        print(f"\nRunning Mann-Kendall tests...")
        results_df = run_analysis(df, label)
        print_results(results_df, label)
        all_results[label] = (df, results_df, suffix)

        if args.output:
            csv_out  = f"{args.output}_{suffix}.csv"
            xlsx_out = f"{args.output}_{suffix}.xlsx"
            results_df.to_csv(csv_out, index=False)
            results_df.to_excel(xlsx_out, index=False)
            print(f"\n  Saved: {csv_out}  and  {xlsx_out}")

    # Run Spearman correlation if both files were provided
    if len(all_results) == 2:
        items = list(all_results.values())
        # Determine which is participation and which is top achievement
        df_par = items[0][0] if 'Participation' in list(all_results.keys())[0] else items[1][0]
        df_ta  = items[1][0] if 'Achievement'   in list(all_results.keys())[1] else items[0][0]

        print(f"\n{'=' * 65}")
        print(f"  SPEARMAN CORRELATION (RQ3) -- MFR-P vs MFR-TA")
        print(f"{'=' * 65}")
        spearman_df = run_spearman(df_par, df_ta)
        sig = spearman_df['Significant'].sum()
        print(f"  Significant (p < .05): {sig}/{len(spearman_df)}\n")
        print(spearman_df.to_string(index=False))

        if args.output:
            sp_csv  = f"{args.output}_spearman.csv"
            sp_xlsx = f"{args.output}_spearman.xlsx"
            spearman_df.to_csv(sp_csv, index=False)
            spearman_df.to_excel(sp_xlsx, index=False)
            print(f"\n  Saved: {sp_csv}  and  {sp_xlsx}")

    print("\nAnalysis complete.")


if __name__ == '__main__':
    main()
