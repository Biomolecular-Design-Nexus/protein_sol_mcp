#!/usr/bin/env python3
"""
Script: predict_solubility.py
Description: Predict protein solubility from FASTA sequences using the protein-sol pipeline

Original Use Case: examples/use_case_1_predict_solubility.py
Dependencies Removed: Inlined utility functions, simplified error handling

Usage:
    python scripts/predict_solubility.py --input <input_file> --output <output_file>

Example:
    python scripts/predict_solubility.py --input examples/data/example.fasta --output results/prediction
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import sys
from pathlib import Path
from typing import Union, Optional, Dict, Any
import json

# Essential scientific package
import pandas as pd

# Local imports (shared library)
from lib.io import parse_results_csv
from lib.protein_sol import run_protein_sol_prediction

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "show_results": False,
    "cleanup_temp": True,
    "output_format": "csv",
    "include_detailed": True
}

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_predict_solubility(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for protein solubility prediction.

    Args:
        input_file: Path to input FASTA file
        output_file: Path prefix for output files (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: Main computation result (DataFrame)
            - output_files: Dict of generated output file paths
            - metadata: Execution metadata

    Example:
        >>> result = run_predict_solubility("input.fasta", "output")
        >>> print(result['output_files']['csv'])
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Determine output prefix
    if output_file:
        output_prefix = str(output_file)
    else:
        output_prefix = input_file.stem

    # Run prediction using shared library
    output_files = run_protein_sol_prediction(
        input_fasta=input_file,
        output_prefix=output_prefix,
        cleanup=config['cleanup_temp']
    )

    # Parse main results
    result_df = None
    if 'csv' in output_files:
        result_df = parse_results_csv(output_files['csv'])

    return {
        "result": result_df,
        "output_files": output_files,
        "metadata": {
            "input_file": str(input_file),
            "config": config,
            "success": True
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
        """
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input FASTA file containing protein sequences')
    parser.add_argument('--output', '-o',
                       help='Output prefix for result files (default: input filename)')
    parser.add_argument('--config', '-c',
                       help='Config file (JSON)')
    parser.add_argument('--show-results', action='store_true',
                       help='Display results summary after prediction')

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI args
    cli_overrides = {}
    if args.show_results:
        cli_overrides['show_results'] = True

    # Run
    try:
        result = run_predict_solubility(
            input_file=args.input,
            output_file=args.output,
            config=config,
            **cli_overrides
        )

        print(f"✅ Prediction completed successfully!")
        print(f"Output files:")
        for file_type, path in result['output_files'].items():
            print(f"  {file_type}: {path}")

        # Show results summary if requested
        if args.show_results and result['result'] is not None:
            print(f"\nResults summary:")
            print(result['result'].to_string(index=False))

        # Save JSON output if --output specified with .json extension (for MCP job manager)
        if args.output and str(args.output).endswith('.json'):
            # Convert DataFrame to dict for JSON serialization
            json_result = result.copy()
            if json_result['result'] is not None:
                json_result['result'] = json_result['result'].to_dict('records')
            with open(args.output, 'w') as f:
                json.dump(json_result, f, indent=2, default=str)

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()