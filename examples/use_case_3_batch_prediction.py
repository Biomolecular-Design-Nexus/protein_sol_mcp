#!/usr/bin/env python3
"""
Batch Protein Solubility Prediction

This script processes multiple FASTA files or directories of FASTA files
for batch protein solubility prediction.

Usage:
    python use_case_3_batch_prediction.py --input examples/data/
    python use_case_3_batch_prediction.py --files file1.fasta file2.fasta
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
import pandas as pd
from pathlib import Path
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def find_fasta_files(input_path):
    """
    Find all FASTA files in a directory or return single file.

    Args:
        input_path (str): Path to file or directory

    Returns:
        list: List of FASTA file paths
    """
    path = Path(input_path)

    if path.is_file():
        return [str(path)]
    elif path.is_dir():
        fasta_files = []
        # Common FASTA extensions
        extensions = ['*.fasta', '*.fa', '*.fas', '*.faa', '*.seq']

        for ext in extensions:
            fasta_files.extend(path.glob(ext))
            fasta_files.extend(path.glob(f"**/{ext}"))  # Recursive

        return [str(f) for f in fasta_files]
    else:
        return []


def process_single_file(fasta_file, output_dir, repo_dir):
    """
    Process a single FASTA file.

    Args:
        fasta_file (str): Path to FASTA file
        output_dir (str): Output directory
        repo_dir (str): Repository directory

    Returns:
        dict: Processing results
    """
    try:
        file_stem = Path(fasta_file).stem
        print(f"Processing: {fasta_file}")

        # Create working directory
        working_dir = tempfile.mkdtemp(prefix=f"protein_sol_{file_stem}_")

        # Copy required files
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

        # Copy input file
        input_file = Path(working_dir) / "input.fasta"
        shutil.copy2(fasta_file, input_file)

        # Make executable
        wrapper_script = Path(working_dir) / "multiple_prediction_wrapper_export.sh"
        wrapper_script.chmod(0o755)

        # Run prediction
        start_time = time.time()
        cmd = ["bash", "multiple_prediction_wrapper_export.sh", "input.fasta"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)
        end_time = time.time()

        if result.returncode != 0:
            return {
                'file': fasta_file,
                'status': 'failed',
                'error': result.stderr,
                'processing_time': end_time - start_time
            }

        # Copy results
        output_files = {}
        base_name = "input.fasta"

        csv_file = Path(working_dir) / f"{base_name}-protein_sol.csv"
        if csv_file.exists():
            output_csv = Path(output_dir) / f"{file_stem}_solubility_results.csv"
            shutil.copy2(csv_file, output_csv)
            output_files['csv'] = str(output_csv)

        prediction_file = Path(working_dir) / f"{base_name}-protein_sol_prediction.txt"
        if prediction_file.exists():
            output_pred = Path(output_dir) / f"{file_stem}_detailed_prediction.txt"
            shutil.copy2(prediction_file, output_pred)
            output_files['prediction'] = str(output_pred)

        # Clean up
        shutil.rmtree(working_dir)

        return {
            'file': fasta_file,
            'status': 'success',
            'output_files': output_files,
            'processing_time': end_time - start_time
        }

    except Exception as e:
        return {
            'file': fasta_file,
            'status': 'failed',
            'error': str(e),
            'processing_time': 0
        }


def combine_results(csv_files, output_file):
    """
    Combine multiple CSV results into a single file.

    Args:
        csv_files (list): List of CSV file paths
        output_file (str): Output combined CSV file
    """
    all_data = []

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Add source file column
            df['source_file'] = Path(csv_file).stem.replace('_solubility_results', '')
            all_data.append(df)
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.to_csv(output_file, index=False)
        return combined_df
    else:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Batch processing of protein solubility predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all FASTA files in a directory
  python use_case_3_batch_prediction.py --input examples/data/

  # Process specific files
  python use_case_3_batch_prediction.py --files file1.fasta file2.fasta

  # Parallel processing with custom number of workers
  python use_case_3_batch_prediction.py --input data/ --workers 4

Output:
  Creates individual result files for each input file plus:
  - combined_solubility_results.csv: All results in one file
  - batch_processing_report.txt: Processing summary
        """)

    parser.add_argument("--input", "-i",
                       help="Input directory containing FASTA files")
    parser.add_argument("--files", nargs="+",
                       help="Specific FASTA files to process")
    parser.add_argument("--output", "-o", default="batch_results",
                       help="Output directory (default: batch_results)")
    parser.add_argument("--workers", "-w", type=int, default=2,
                       help="Number of parallel workers (default: 2)")
    parser.add_argument("--combine", action="store_true", default=True,
                       help="Combine all results into single CSV (default: True)")

    args = parser.parse_args()

    # Validate input
    if not args.input and not args.files:
        print("Error: Must provide either --input directory or --files")
        sys.exit(1)

    # Find FASTA files
    fasta_files = []
    if args.input:
        fasta_files.extend(find_fasta_files(args.input))
    if args.files:
        for file in args.files:
            if Path(file).exists():
                fasta_files.append(file)
            else:
                print(f"Warning: File {file} not found")

    if not fasta_files:
        print("Error: No FASTA files found")
        sys.exit(1)

    print(f"Found {len(fasta_files)} FASTA files to process")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get repository directory
    script_dir = Path(__file__).parent.parent
    repo_dir = script_dir / "repo" / "protein-sol"

    if not repo_dir.exists():
        print(f"Error: Protein-sol repository not found at {repo_dir}")
        sys.exit(1)

    # Process files
    results = []
    failed_files = []
    successful_files = []

    print(f"Processing with {args.workers} parallel workers...")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all jobs
        futures = {
            executor.submit(process_single_file, fasta_file, output_dir, repo_dir): fasta_file
            for fasta_file in fasta_files
        }

        # Collect results
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result['status'] == 'success':
                successful_files.append(result['file'])
                print(f"✓ {Path(result['file']).name} completed in {result['processing_time']:.1f}s")
            else:
                failed_files.append(result['file'])
                print(f"✗ {Path(result['file']).name} failed: {result.get('error', 'Unknown error')}")

    end_time = time.time()
    total_time = end_time - start_time

    # Combine results if requested
    combined_df = None
    if args.combine and successful_files:
        csv_files = []
        for result in results:
            if result['status'] == 'success' and 'csv' in result['output_files']:
                csv_files.append(result['output_files']['csv'])

        if csv_files:
            combined_file = output_dir / "combined_solubility_results.csv"
            combined_df = combine_results(csv_files, combined_file)
            if combined_df is not None:
                print(f"\nCombined results saved to: {combined_file}")

    # Generate report
    report_file = output_dir / "batch_processing_report.txt"
    with open(report_file, 'w') as f:
        f.write("Batch Protein Solubility Prediction Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total files processed: {len(fasta_files)}\n")
        f.write(f"Successful: {len(successful_files)}\n")
        f.write(f"Failed: {len(failed_files)}\n")
        f.write(f"Total processing time: {total_time:.1f} seconds\n")
        f.write(f"Average time per file: {total_time/len(fasta_files):.1f} seconds\n\n")

        if successful_files:
            f.write("Successful files:\n")
            for file in successful_files:
                f.write(f"  ✓ {file}\n")

        if failed_files:
            f.write("\nFailed files:\n")
            for file in failed_files:
                f.write(f"  ✗ {file}\n")

        if combined_df is not None:
            f.write(f"\nCombined results summary:\n")
            f.write(f"  Total proteins analyzed: {len(combined_df)}\n")
            f.write(f"  Average solubility: {combined_df['percent-sol'].mean():.1f}%\n")
            f.write(f"  Solubility range: {combined_df['percent-sol'].min():.1f}% - {combined_df['percent-sol'].max():.1f}%\n")

    print(f"\nBatch processing completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Report saved to: {report_file}")
    print(f"Success rate: {len(successful_files)}/{len(fasta_files)} ({len(successful_files)/len(fasta_files)*100:.1f}%)")


if __name__ == "__main__":
    main()