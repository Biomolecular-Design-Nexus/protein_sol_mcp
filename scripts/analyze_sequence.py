#!/usr/bin/env python3
"""
Script: analyze_sequence.py
Description: Analyze amino acid composition and physicochemical properties of protein sequences

Original Use Case: examples/use_case_2_sequence_analysis.py
Dependencies Removed: Inlined FASTA writing, simplified analysis workflow

Usage:
    python scripts/analyze_sequence.py --input <input_file> --output <output_file>
    python scripts/analyze_sequence.py --sequence <sequence> --id <identifier>

Example:
    python scripts/analyze_sequence.py --input examples/data/example.fasta --output results/analysis
    python scripts/analyze_sequence.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein"
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import sys
import tempfile
import re
from pathlib import Path
from typing import Union, Optional, Dict, Any
import json

# Local imports (shared library)
from lib.io import write_fasta, read_fasta
from lib.protein_sol import run_composition_analysis

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "basic_only": False,
    "include_composition": True,
    "include_properties": True,
    "output_format": "txt"
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def calculate_basic_stats(sequence: str) -> Dict[str, Any]:
    """Calculate basic sequence statistics. Inlined from repo analysis."""
    # Remove any whitespace and convert to uppercase
    seq = re.sub(r'\s+', '', sequence.upper())

    # Amino acid counts
    aa_counts = {}
    for aa in 'ACDEFGHIKLMNPQRSTVWY':
        aa_counts[aa] = seq.count(aa)

    total_aa = sum(aa_counts.values())

    # Basic properties
    hydrophobic = 'AILMFPWV'
    charged = 'DEKR'
    polar = 'NQSTY'

    hydrophobic_count = sum(seq.count(aa) for aa in hydrophobic)
    charged_count = sum(seq.count(aa) for aa in charged)
    polar_count = sum(seq.count(aa) for aa in polar)

    return {
        'length': len(seq),
        'molecular_weight': total_aa * 110,  # Approximate
        'hydrophobic_residues': hydrophobic_count,
        'hydrophobic_percent': (hydrophobic_count / total_aa * 100) if total_aa > 0 else 0,
        'charged_residues': charged_count,
        'charged_percent': (charged_count / total_aa * 100) if total_aa > 0 else 0,
        'polar_residues': polar_count,
        'polar_percent': (polar_count / total_aa * 100) if total_aa > 0 else 0,
        'amino_acid_composition': aa_counts
    }

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_analyze_sequence(
    input_file: Optional[Union[str, Path]] = None,
    sequence: Optional[str] = None,
    sequence_id: Optional[str] = None,
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for sequence composition and property analysis.

    Args:
        input_file: Path to input FASTA file (alternative to sequence)
        sequence: Single protein sequence (alternative to input_file)
        sequence_id: Identifier for single sequence
        output_file: Path prefix for output files (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: Analysis results dict
            - output_files: Dict of generated output file paths
            - metadata: Execution metadata

    Example:
        >>> result = run_analyze_sequence(sequence="MVKVYA", sequence_id="test")
        >>> print(result['result']['basic_stats'])
    """
    # Setup
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Handle input modes
    if sequence and sequence_id:
        # Single sequence mode
        if output_file:
            output_prefix = str(output_file)
        else:
            output_prefix = sequence_id

        # Create temporary FASTA file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as tmp:
            write_fasta(sequence, sequence_id, tmp.name)
            temp_fasta = tmp.name

    elif input_file:
        # FASTA file mode
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if output_file:
            output_prefix = str(output_file)
        else:
            output_prefix = input_path.stem

        temp_fasta = str(input_path)

    else:
        raise ValueError("Either input_file or (sequence + sequence_id) must be provided")

    # Basic only mode
    if config['basic_only']:
        sequences = read_fasta(temp_fasta)
        results = {}
        for seq_id, seq in sequences:
            results[seq_id] = calculate_basic_stats(seq)

        return {
            "result": {
                "basic_stats": results,
                "mode": "basic_only"
            },
            "output_files": {},
            "metadata": {
                "config": config,
                "sequence_count": len(sequences)
            }
        }

    # Full analysis mode - run composition analysis
    output_files = {}
    analysis_result = {}

    try:
        if config['include_composition'] or config['include_properties']:
            comp_files = run_composition_analysis(temp_fasta, output_prefix)
            output_files.update(comp_files)
            analysis_result['analysis_files'] = comp_files

        # Add basic stats for each sequence
        sequences = read_fasta(temp_fasta)
        basic_stats = {}
        for seq_id, seq in sequences:
            basic_stats[seq_id] = calculate_basic_stats(seq)
        analysis_result['basic_stats'] = basic_stats

        return {
            "result": analysis_result,
            "output_files": output_files,
            "metadata": {
                "config": config,
                "sequence_count": len(sequences),
                "temp_fasta": temp_fasta if sequence else None
            }
        }

    finally:
        # Clean up temp file if we created one
        if sequence and Path(temp_fasta).exists():
            Path(temp_fasta).unlink()


# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze FASTA file
  python scripts/analyze_sequence.py --input examples/data/example.fasta

  # Analyze single sequence
  python scripts/analyze_sequence.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein"

  # Basic analysis only (no files)
  python scripts/analyze_sequence.py --sequence "MVLSEGEWQL" --basic-only

Output files (full mode):
  PREFIX_composition_analysis.txt    - Amino acid composition percentages
  PREFIX_properties_analysis.txt     - Physicochemical properties analysis
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i',
                           help='Input FASTA file containing protein sequences')
    input_group.add_argument('--sequence', '-s',
                           help='Single protein sequence to analyze')

    # Other options
    parser.add_argument('--id',
                       help='Identifier for single sequence (required with --sequence)')
    parser.add_argument('--output', '-o',
                       help='Output prefix for result files (default: input filename or sequence ID)')
    parser.add_argument('--config', '-c',
                       help='Config file (JSON)')
    parser.add_argument('--basic-only', action='store_true',
                       help='Show only basic statistics (no output files)')

    args = parser.parse_args()

    # Validate arguments
    if args.sequence and not args.id:
        parser.error("--id is required when using --sequence")

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI args
    cli_overrides = {}
    if args.basic_only:
        cli_overrides['basic_only'] = True

    # Run
    try:
        result = run_analyze_sequence(
            input_file=args.input,
            sequence=args.sequence,
            sequence_id=args.id,
            output_file=args.output,
            config=config,
            **cli_overrides
        )

        if result['metadata']['config']['basic_only']:
            # Display basic stats immediately
            print("Basic sequence analysis:")
            for seq_id, stats in result['result']['basic_stats'].items():
                print(f"\nSequence: {seq_id}")
                print(f"  Length: {stats['length']}")
                print(f"  Hydrophobic: {stats['hydrophobic_percent']:.1f}%")
                print(f"  Charged: {stats['charged_percent']:.1f}%")
                print(f"  Polar: {stats['polar_percent']:.1f}%")
        else:
            print(f"✅ Sequence analysis completed!")
            if result['output_files']:
                print(f"Output files:")
                for file_type, path in result['output_files'].items():
                    print(f"  {file_type}: {path}")

            print(f"\nAnalyzed {result['metadata']['sequence_count']} sequence(s)")

        # Save JSON output if --output specified with .json extension (for MCP job manager)
        if args.output and str(args.output).endswith('.json'):
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()