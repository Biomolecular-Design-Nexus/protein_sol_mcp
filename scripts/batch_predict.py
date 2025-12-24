#!/usr/bin/env python3
"""
Script: batch_predict.py
Description: Process multiple FASTA files for batch protein solubility prediction

Original Use Case: examples/use_case_3_batch_prediction.py
Dependencies Removed: Inlined file discovery, simplified parallel processing

Usage:
    python scripts/batch_predict.py --input <directory> --workers <num>
    python scripts/batch_predict.py --files <file1> <file2> ... --workers <num>

Example:
    python scripts/batch_predict.py --input examples/data/ --workers 2
    python scripts/batch_predict.py --files file1.fasta file2.fasta --workers 4
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import sys
import time
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Local imports (shared library)
from lib.io import find_fasta_files
from lib.protein_sol import run_protein_sol_prediction

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "max_workers": 2,
    "timeout_per_file": 300,  # 5 minutes per file
    "continue_on_error": True,
    "cleanup_temp": True,
    "generate_report": True
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def process_single_file(file_path: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Process a single FASTA file for solubility prediction.

    Args:
        file_path: Path to FASTA file
        output_dir: Optional output directory

    Returns:
        Dict with processing results
    """
    start_time = time.time()
    file_path = Path(file_path)

    try:
        # Determine output prefix
        if output_dir:
            output_prefix = output_dir / file_path.stem
        else:
            output_prefix = file_path.stem

        # Run prediction
        output_files = run_protein_sol_prediction(
            input_fasta=file_path,
            output_prefix=str(output_prefix),
            cleanup=True
        )

        processing_time = time.time() - start_time

        return {
            'file': str(file_path),
            'status': 'success',
            'processing_time': processing_time,
            'output_files': output_files,
            'error': None
        }

    except Exception as e:
        processing_time = time.time() - start_time
        return {
            'file': str(file_path),
            'status': 'error',
            'processing_time': processing_time,
            'output_files': {},
            'error': str(e)
        }


def generate_batch_report(results: List[Dict[str, Any]], output_file: str) -> None:
    """Generate a summary report of batch processing."""
    total_files = len(results)
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = total_files - successful
    total_time = sum(r['processing_time'] for r in results)
    avg_time = total_time / total_files if total_files > 0 else 0

    report = f"""Batch Processing Report
========================

Files Processed: {total_files}
Successful: {successful}
Failed: {failed}
Success Rate: {(successful/total_files*100):.1f}%

Total Processing Time: {total_time:.2f} seconds
Average Time per File: {avg_time:.2f} seconds

Detailed Results:
"""

    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        report += f"\n{status_icon} {result['file']} ({result['processing_time']:.2f}s)"
        if result['error']:
            report += f" - Error: {result['error']}"

    with open(output_file, 'w') as f:
        f.write(report)

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_batch_predict(
    input_path: Optional[Union[str, Path]] = None,
    files: Optional[List[Union[str, Path]]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for batch protein solubility prediction.

    Args:
        input_path: Directory containing FASTA files (alternative to files)
        files: List of specific FASTA files to process (alternative to input_path)
        output_dir: Directory for output files (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - results: List of processing results for each file
            - summary: Summary statistics
            - report_file: Path to generated report (if enabled)
            - metadata: Execution metadata

    Example:
        >>> result = run_batch_predict(input_path="data/", max_workers=4)
        >>> print(f"Processed {len(result['results'])} files")
    """
    # Setup
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Determine file list
    if files:
        fasta_files = [str(f) for f in files]
    elif input_path:
        fasta_files = find_fasta_files(input_path)
    else:
        raise ValueError("Either input_path or files must be provided")

    if not fasta_files:
        raise ValueError("No FASTA files found")

    # Setup output directory
    output_dir_path = None
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Process files in parallel
    results = []
    start_time = time.time()

    print(f"Processing {len(fasta_files)} files with {config['max_workers']} workers...")

    with ThreadPoolExecutor(max_workers=config['max_workers']) as executor:
        # Submit all jobs
        future_to_file = {
            executor.submit(process_single_file, file_path, output_dir_path): file_path
            for file_path in fasta_files
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            result = future.result()
            results.append(result)

            # Progress update
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {Path(result['file']).name} ({result['processing_time']:.2f}s)")

    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['status'] == 'success')

    # Generate summary
    summary = {
        'total_files': len(results),
        'successful': successful,
        'failed': len(results) - successful,
        'success_rate': (successful / len(results) * 100) if results else 0,
        'total_time': total_time,
        'average_time': sum(r['processing_time'] for r in results) / len(results) if results else 0
    }

    # Generate report if enabled
    report_file = None
    if config['generate_report']:
        report_file = "batch_processing_report.txt"
        generate_batch_report(results, report_file)

    return {
        "results": results,
        "summary": summary,
        "report_file": report_file,
        "metadata": {
            "config": config,
            "input_files": fasta_files,
            "output_dir": str(output_dir_path) if output_dir_path else None
        }
    }


# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process directory with 2 workers
  python scripts/batch_predict.py --input examples/data/ --workers 2

  # Process specific files with 4 workers
  python scripts/batch_predict.py --files file1.fasta file2.fasta --workers 4

  # Process with custom output directory
  python scripts/batch_predict.py --input data/ --output results/ --workers 2

Output:
  - Individual result files for each input file
  - batch_processing_report.txt with summary statistics
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i',
                           help='Directory containing FASTA files to process')
    input_group.add_argument('--files', nargs='+',
                           help='Specific FASTA files to process')

    # Other options
    parser.add_argument('--output', '-o',
                       help='Output directory for result files')
    parser.add_argument('--workers', '-w', type=int, default=2,
                       help='Number of parallel workers (default: 2)')
    parser.add_argument('--config', '-c',
                       help='Config file (JSON)')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip generating summary report')

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI args
    cli_overrides = {
        'max_workers': args.workers
    }
    if args.no_report:
        cli_overrides['generate_report'] = False

    # Run
    try:
        result = run_batch_predict(
            input_path=args.input,
            files=args.files,
            output_dir=args.output,
            config=config,
            **cli_overrides
        )

        summary = result['summary']
        print(f"\n✅ Batch processing completed!")
        print(f"Files processed: {summary['total_files']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Total time: {summary['total_time']:.2f} seconds")
        print(f"Average time per file: {summary['average_time']:.2f} seconds")

        if result['report_file']:
            print(f"Report saved to: {result['report_file']}")

        # Save JSON output if --output specified (for MCP job manager)
        if args.output and str(args.output).endswith('.json'):
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)

        # Exit with error code if any files failed and continue_on_error is False
        config_used = {**DEFAULT_CONFIG, **(config or {}), **cli_overrides}
        if not config_used['continue_on_error'] and summary['failed'] > 0:
            sys.exit(1)

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()