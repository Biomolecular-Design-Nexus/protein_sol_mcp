#!/usr/bin/env python3
"""
Protein Solubility Prediction Tool

This script provides a Python wrapper for the protein-sol Perl pipeline
to predict protein solubility from amino acid sequences.

Based on:
- Hebditch et al (2017) Bioinformatics 33:3098-3100
- University of Manchester protein-sol server
- www.protein-sol.manchester.ac.uk

Usage:
    python use_case_1_predict_solubility.py --input examples/data/example.fasta
    python use_case_1_predict_solubility.py --input myprotein.fasta --output myresults
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
import pandas as pd
from pathlib import Path


def run_protein_sol_prediction(input_fasta, output_prefix=None, working_dir=None):
    """
    Run protein solubility prediction using the Perl pipeline.

    Args:
        input_fasta (str): Path to input FASTA file
        output_prefix (str): Optional output prefix. If None, uses input filename
        working_dir (str): Optional working directory. If None, uses temp directory

    Returns:
        dict: Dictionary containing paths to output files
    """

    if output_prefix is None:
        output_prefix = Path(input_fasta).stem

    # Get the script directory
    script_dir = Path(__file__).parent.parent
    repo_dir = script_dir / "repo" / "protein-sol"

    if not repo_dir.exists():
        raise FileNotFoundError(f"Protein-sol repository not found at {repo_dir}")

    # Create working directory if needed
    if working_dir is None:
        working_dir = tempfile.mkdtemp(prefix="protein_sol_")
        temp_dir = True
    else:
        Path(working_dir).mkdir(parents=True, exist_ok=True)
        temp_dir = False

    try:
        # Copy required files to working directory
        required_files = [
            "multiple_prediction_wrapper_export.sh",
            "fasta_seq_reformat_export.pl",
            "seq_compositions_perc_pipeline_export.pl",
            "server_prediction_seq_export.pl",
            "seq_props_ALL_export.pl",
            "profiles_gather_export.pl",
            "ss_propensities.txt",
            "seq_reference_data.txt"
        ]

        for file in required_files:
            src = repo_dir / file
            dst = Path(working_dir) / file
            if src.exists():
                shutil.copy2(src, dst)
            else:
                print(f"Warning: Required file {file} not found")

        # Copy input file to working directory
        input_file = Path(working_dir) / "input.fasta"
        shutil.copy2(input_fasta, input_file)

        # Make wrapper script executable
        wrapper_script = Path(working_dir) / "multiple_prediction_wrapper_export.sh"
        wrapper_script.chmod(0o755)

        # Run prediction
        print(f"Running protein solubility prediction on {input_fasta}...")

        cmd = ["bash", "multiple_prediction_wrapper_export.sh", "input.fasta"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error running prediction: {result.stderr}")
            return None

        # Collect output files
        output_files = {}
        base_name = "input.fasta"

        # Main prediction results
        csv_file = Path(working_dir) / f"{base_name}-protein_sol.csv"
        prediction_file = Path(working_dir) / f"{base_name}-protein_sol_prediction.txt"
        composition_file = Path(working_dir) / f"{base_name}-protein_sol_composition.txt"
        log_file = Path(working_dir) / f"{base_name}-protein_sol.log"

        # Copy results to final location with custom prefix
        if csv_file.exists():
            final_csv = f"{output_prefix}_solubility_results.csv"
            shutil.copy2(csv_file, final_csv)
            output_files['csv'] = final_csv

        if prediction_file.exists():
            final_prediction = f"{output_prefix}_detailed_prediction.txt"
            shutil.copy2(prediction_file, final_prediction)
            output_files['prediction'] = final_prediction

        if composition_file.exists():
            final_composition = f"{output_prefix}_composition.txt"
            shutil.copy2(composition_file, final_composition)
            output_files['composition'] = final_composition

        if log_file.exists():
            final_log = f"{output_prefix}_prediction.log"
            shutil.copy2(log_file, final_log)
            output_files['log'] = final_log

        return output_files

    finally:
        # Clean up temporary directory
        if temp_dir and Path(working_dir).exists():
            shutil.rmtree(working_dir)


def parse_results_csv(csv_file):
    """
    Parse the CSV results file and return a pandas DataFrame.

    Args:
        csv_file (str): Path to CSV results file

    Returns:
        pandas.DataFrame: Parsed results
    """
    try:
        df = pd.read_csv(csv_file)
        return df
    except Exception as e:
        print(f"Error parsing CSV file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Predict protein solubility from FASTA sequences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python use_case_1_predict_solubility.py --input examples/data/example.fasta
  python use_case_1_predict_solubility.py --input myprotein.fasta --output myresults

Output files:
  PREFIX_solubility_results.csv      - Main prediction results (CSV format)
  PREFIX_detailed_prediction.txt     - Detailed predictions with all features
  PREFIX_composition.txt             - Amino acid composition analysis
  PREFIX_prediction.log              - Processing log

The CSV file contains:
  - ID: Protein identifier from FASTA
  - sequence: Protein sequence
  - percent-sol: Percentage solubility prediction
  - scaled-sol: Scaled solubility score (0-1)
  - population-sol: Population-based solubility estimate
  - pI: Isoelectric point
        """)

    parser.add_argument("--input", "-i", required=True,
                       help="Input FASTA file containing protein sequences")
    parser.add_argument("--output", "-o",
                       help="Output prefix for result files (default: input filename)")
    parser.add_argument("--working-dir",
                       help="Working directory for temporary files")
    parser.add_argument("--show-results", action="store_true",
                       help="Display results summary after prediction")

    args = parser.parse_args()

    # Check input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file {args.input} not found")
        sys.exit(1)

    # Run prediction
    try:
        output_files = run_protein_sol_prediction(
            args.input,
            args.output,
            args.working_dir
        )

        if output_files is None:
            print("Prediction failed")
            sys.exit(1)

        print(f"\nPrediction completed successfully!")
        print(f"Output files:")
        for file_type, path in output_files.items():
            print(f"  {file_type}: {path}")

        # Show results summary if requested
        if args.show_results and 'csv' in output_files:
            print(f"\nResults summary:")
            df = parse_results_csv(output_files['csv'])
            if df is not None:
                print(df.to_string(index=False))

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()