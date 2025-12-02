#!/usr/bin/env python3
"""
Python wrapper for protein-sol solubility prediction pipeline.
Replicates the functionality of multiple_prediction_wrapper_export.sh
"""

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path


def parse_fasta(fasta_file):
    """
    Parse FASTA file and extract sequences.

    Returns:
        dict: Dictionary mapping sequence ID to sequence string
    """
    sequences = {}
    current_id = None
    current_seq = []

    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                # Save previous sequence if exists
                if current_id is not None:
                    sequences[current_id] = ''.join(current_seq)
                # Start new sequence
                current_id = line[1:]  # Remove '>' character
                current_seq = []
            else:
                current_seq.append(line)

        # Save last sequence
        if current_id is not None:
            sequences[current_id] = ''.join(current_seq)

    return sequences


def create_csv_output(fasta_file, prediction_file, output_file):
    """
    Create CSV output file combining sequences and predictions.

    Args:
        fasta_file: Path to original FASTA file
        prediction_file: Path to seq_prediction.txt
        output_file: Path to output CSV file
    """
    # Parse sequences from FASTA
    sequences = parse_fasta(fasta_file)

    # Parse predictions
    predictions = {}
    try:
        with open(prediction_file, 'r') as f:
            for line in f:
                if line.startswith("SEQUENCE PREDICTIONS,"):
                    parts = line.strip().split(',')
                    if len(parts) >= 6:
                        seq_id = parts[1].lstrip('>')  # Remove '>' if present
                        predictions[seq_id] = {
                            'percent-sol': parts[2].strip(),
                            'scaled-sol': parts[3].strip(),
                            'population-sol': parts[4].strip(),
                            'pI': parts[5].strip()
                        }
    except FileNotFoundError:
        print(f"Error: Prediction file '{prediction_file}' not found", file=sys.stderr)
        return False

    # Create CSV output
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'sequence', 'percent-sol', 'scaled-sol', 'population-sol', 'pI'])

            for seq_id, sequence in sequences.items():
                # Try exact match first
                if seq_id in predictions:
                    pred = predictions[seq_id]
                else:
                    # Try matching by the first part before space (for headers with descriptions)
                    seq_id_base = seq_id.split()[0] if ' ' in seq_id else seq_id
                    pred = None
                    for pred_id, pred_data in predictions.items():
                        if pred_id == seq_id_base or seq_id_base == pred_id.split()[0]:
                            pred = pred_data
                            break
                    if pred is None:
                        continue

                writer.writerow([
                    seq_id,
                    sequence,
                    pred['percent-sol'],
                    pred['scaled-sol'],
                    pred['population-sol'],
                    pred['pI']
                ])

        print(f"✓ CSV output saved to {output_file}")
        return True

    except Exception as e:
        print(f"Error creating CSV output: {e}", file=sys.stderr)
        return False


def run_perl_script(script_name, log_file, verbose=True):
    """Run a Perl script and append output to log file."""
    print(f"Running {script_name}...")

    try:
        result = subprocess.run(
            ["perl", script_name],
            capture_output=True,
            text=True,
            check=True
        )

        # Write to log file
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Script: {script_name}\n")
            f.write(f"{'='*60}\n")
            if result.stdout:
                f.write(result.stdout)
            if result.stderr:
                f.write("STDERR:\n")
                f.write(result.stderr)

        # Print to console if verbose
        if verbose:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}", file=sys.stderr)

        print(f"✓ {script_name} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        error_msg = f"Error running {script_name}: {e}"
        print(error_msg, file=sys.stderr)

        with open(log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"ERROR in {script_name}\n")
            f.write(f"{'='*60}\n")
            f.write(f"{error_msg}\n")
            if e.stdout:
                f.write(e.stdout)
            if e.stderr:
                f.write("STDERR:\n")
                f.write(e.stderr)

        return False


def parse_and_print_predictions(prediction_file):
    """
    Parse and print prediction results from seq_prediction.txt.

    Extracts: ID, percent-sol, scaled-sol, population-sol, pI
    """
    try:
        with open(prediction_file, 'r') as f:
            lines = f.readlines()

        # Find and parse SEQUENCE PREDICTIONS lines
        predictions = []
        for line in lines:
            if line.startswith("SEQUENCE PREDICTIONS,"):
                parts = line.strip().split(',')
                if len(parts) >= 6:
                    seq_id = parts[1]  # ID like >P00547
                    percent_sol = parts[2].strip()
                    scaled_sol = parts[3].strip()
                    population_sol = parts[4].strip()
                    pi = parts[5].strip()

                    predictions.append({
                        'ID': seq_id,
                        'percent-sol': percent_sol,
                        'scaled-sol': scaled_sol,
                        'population-sol': population_sol,
                        'pI': pi
                    })

        if predictions:
            # Print header
            print(f"{'ID':<20} {'percent-sol':<15} {'scaled-sol':<15} {'population-sol':<15} {'pI':<10}")
            print("-" * 80)

            # Print each prediction
            for pred in predictions:
                print(f"{pred['ID']:<20} {pred['percent-sol']:<15} {pred['scaled-sol']:<15} {pred['population-sol']:<15} {pred['pI']:<10}")
        else:
            print("No predictions found in output file.")

    except FileNotFoundError:
        print(f"Error: Prediction file '{prediction_file}' not found", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing predictions: {e}", file=sys.stderr)


def predict_solubility(fasta_input, verbose=True):
    """
    Run the protein-sol prediction pipeline.

    Args:
        fasta_input: Path to input FASTA file
        verbose: Whether to print detailed logs to console

    Returns:
        bool: True if successful, False otherwise
    """
    # Get absolute paths
    original_dir = Path.cwd()
    fasta_path = Path(fasta_input).resolve()

    if not fasta_path.exists():
        print(f"Error: Input file '{fasta_input}' not found", file=sys.stderr)
        return False

    # Find protein-sol directory relative to this script's location
    script_dir = Path(__file__).resolve().parent
    protein_sol_dir = script_dir / "protein-sol"
    if not protein_sol_dir.exists():
        print(f"Error: protein-sol directory not found at {protein_sol_dir}", file=sys.stderr)
        return False

    print(f"\n{'='*60}")
    print("Starting Protein-Sol Prediction Pipeline")
    print(f"Input: {fasta_input}")
    print(f"Working directory: {protein_sol_dir}")
    print(f"{'='*60}\n")

    # Store original fasta filename and directory for output naming
    original_fasta_name = fasta_path.name
    output_dir = fasta_path.parent

    try:
        # Change to protein-sol directory
        import os
        os.chdir(protein_sol_dir)

        # Use a simple local filename
        local_fasta = "input.fasta"
        shutil.copy(fasta_path, local_fasta)

        log_file = "run_log"

        # Initialize log file
        with open(log_file, 'w') as f:
            f.write("Protein-Sol Prediction Pipeline\n")
            f.write(f"Input file: {fasta_input}\n")
            f.write("="*60 + "\n")
        # Step 1: Reformat FASTA
        print("Step 1: Reformatting FASTA file...")
        shutil.copy(local_fasta, "reformat.in")

        if not run_perl_script("fasta_seq_reformat_export.pl", log_file, verbose):
            os.chdir(original_dir)
            return False

        # Backup original and replace with reformatted
        shutil.copy(local_fasta, f"{local_fasta}_ORIGINAL")
        shutil.move("reformat_out", local_fasta)
        print(f"✓ Original file backed up to {local_fasta}_ORIGINAL\n")

        # Step 2: Calculate sequence composition
        print("Step 2: Calculating sequence composition...")
        shutil.copy(local_fasta, "composition.in")

        if not run_perl_script("seq_compositions_perc_pipeline_export.pl", log_file, verbose):
            os.chdir(original_dir)
            return False

        shutil.move("composition_all.out", "seq_composition.txt")
        print("✓ Composition data saved to seq_composition.txt\n")

        # Step 3: Make solubility predictions
        print("Step 3: Making solubility predictions...")

        if not run_perl_script("server_prediction_seq_export.pl", log_file, verbose):
            os.chdir(original_dir)
            return False

        print("✓ Predictions generated\n")

        # Step 4: Calculate sequence properties
        print("Step 4: Calculating sequence properties...")
        shutil.copy(local_fasta, "seq_props.in")

        if not run_perl_script("seq_props_ALL_export.pl", log_file, verbose):
            os.chdir(original_dir)
            return False

        print("✓ Sequence properties calculated\n")

        # Step 5: Gather profiles
        print("Step 5: Gathering profiles...")

        if Path("seq_prediction.txt").exists():
            shutil.move("seq_prediction.txt", "seq_prediction_OLD.txt")

        if not run_perl_script("profiles_gather_export.pl", log_file, verbose):
            os.chdir(original_dir)
            return False

        print("✓ Profiles gathered\n")

        # Step 6: Create CSV output
        print("Step 6: Creating CSV output...")
        # Use the backup file since the original was replaced
        backup_fasta = f"{local_fasta}_ORIGINAL"
        csv_output_file = f"{original_fasta_name}-protein_sol.csv"

        if not create_csv_output(backup_fasta, "seq_prediction.txt", csv_output_file):
            print("Warning: Failed to create CSV output", file=sys.stderr)
        print()

        # Step 7: Cleanup intermediate files
        print("Step 7: Cleaning up intermediate files...")
        intermediate_files = [
            "bins.txt",
            "reformat.in",
            "seq_props.in",
            "seq_props.out",
            "STYprops.out",
            "composition.in",
            "seq_prediction_OLD.txt"
        ]

        for file in intermediate_files:
            if Path(file).exists():
                Path(file).unlink()

        # Rename log file with proper naming
        log_output_file = f"{original_fasta_name}-protein_sol.log"
        shutil.move(log_file, log_output_file)
        print("✓ Cleanup completed\n")

        # Parse and print prediction results before moving files
        print(f"{'='*60}")
        print("Prediction Results:")
        print(f"{'='*60}")
        parse_and_print_predictions("seq_prediction.txt")
        print()

        # Define output filenames based on input FASTA
        output_prediction_file = f"{original_fasta_name}-protein_sol_prediction.txt"
        output_composition_file = f"{original_fasta_name}-protein_sol_composition.txt"

        # Copy output files to input FASTA directory (only if different from current)
        current_dir = Path.cwd()
        if current_dir != output_dir:
            shutil.copy(csv_output_file, output_dir / csv_output_file)
            shutil.copy("seq_prediction.txt", output_dir / output_prediction_file)
            shutil.copy("seq_composition.txt", output_dir / output_composition_file)
            shutil.copy(log_output_file, output_dir / log_output_file)
        else:
            # Already in the output directory, just rename files
            shutil.move("seq_prediction.txt", output_prediction_file)
            shutil.move("seq_composition.txt", output_composition_file)

        # Change back to original directory
        os.chdir(original_dir)

        print(f"{'='*60}")
        print("Pipeline completed successfully!")
        print(f"{'='*60}")
        print(f"\nOutput files in {output_dir}:")
        print(f"  - {csv_output_file}              : CSV with ID, sequence, and metrics")
        print(f"  - {output_prediction_file} : Main prediction results")
        print(f"  - {output_composition_file}: Sequence composition data")
        print(f"  - {log_output_file}        : Detailed execution log\n")

        return True

    except Exception as e:
        print(f"\nError during pipeline execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        # Make sure to change back to original directory on error
        try:
            os.chdir(original_dir)
        except:
            pass
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Protein-Sol solubility prediction from sequence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python protein_sol_predict.py input.fasta
  python protein_sol_predict.py input.fasta --quiet

Output (saved in same directory as input FASTA):
  input.fasta-protein_sol.csv            - CSV with ID, sequence, and metrics
  input.fasta-protein_sol_prediction.txt - Main prediction results
  input.fasta-protein_sol_composition.txt- Sequence composition data
  input.fasta-protein_sol.log            - Execution log
        """
    )

    parser.add_argument(
        "fasta_file",
        help="Input FASTA file with protein sequence(s)"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress detailed console output (still writes to log)"
    )

    args = parser.parse_args()

    success = predict_solubility(args.fasta_file, verbose=not args.quiet)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
