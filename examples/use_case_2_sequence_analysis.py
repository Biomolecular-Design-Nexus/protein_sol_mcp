#!/usr/bin/env python3
"""
Protein Sequence Composition Analysis

This script analyzes amino acid composition and physicochemical properties
of protein sequences using the protein-sol analysis tools.

Usage:
    python use_case_2_sequence_analysis.py --input examples/data/example.fasta
    python use_case_2_sequence_analysis.py --sequence "MVKVYAPASSANMSVGFDVL"
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
import pandas as pd
from pathlib import Path
import re


def write_fasta(sequence, identifier, output_file):
    """
    Write a sequence to a FASTA file.

    Args:
        sequence (str): Protein sequence
        identifier (str): Sequence identifier
        output_file (str): Output FASTA file path
    """
    with open(output_file, 'w') as f:
        f.write(f">{identifier}\n")
        f.write(f"{sequence}\n")


def analyze_sequence_composition(input_fasta, output_prefix=None):
    """
    Analyze sequence composition and properties.

    Args:
        input_fasta (str): Path to input FASTA file
        output_prefix (str): Output prefix for files

    Returns:
        dict: Analysis results
    """
    if output_prefix is None:
        output_prefix = Path(input_fasta).stem

    # Get the script directory
    script_dir = Path(__file__).parent.parent
    repo_dir = script_dir / "repo" / "protein-sol"

    if not repo_dir.exists():
        raise FileNotFoundError(f"Protein-sol repository not found at {repo_dir}")

    # Create temporary working directory
    working_dir = tempfile.mkdtemp(prefix="protein_composition_")

    try:
        # Copy required files
        required_files = [
            "seq_compositions_perc_pipeline_export.pl",
            "seq_props_ALL_export.pl",
            "ss_propensities.txt"
        ]

        for file in required_files:
            src = repo_dir / file
            dst = Path(working_dir) / file
            if src.exists():
                shutil.copy2(src, dst)

        # Copy and rename input file for pipeline
        composition_input = Path(working_dir) / "composition.in"
        shutil.copy2(input_fasta, composition_input)

        print(f"Analyzing sequence composition for {input_fasta}...")

        # Run composition analysis
        cmd = ["perl", "seq_compositions_perc_pipeline_export.pl"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error in composition analysis: {result.stderr}")
            return None

        # Run sequence properties analysis
        props_input = Path(working_dir) / "seq_props.in"
        shutil.copy2(input_fasta, props_input)

        cmd = ["perl", "seq_props_ALL_export.pl"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error in properties analysis: {result.stderr}")
            return None

        # Collect output files
        output_files = {}

        # Composition output
        comp_out = Path(working_dir) / "composition_all.out"
        if comp_out.exists():
            final_comp = f"{output_prefix}_composition_analysis.txt"
            shutil.copy2(comp_out, final_comp)
            output_files['composition'] = final_comp

        # Properties output
        props_out = Path(working_dir) / "seq_props.out"
        if props_out.exists():
            final_props = f"{output_prefix}_properties_analysis.txt"
            shutil.copy2(props_out, final_props)
            output_files['properties'] = final_props

        return output_files

    finally:
        # Clean up
        if Path(working_dir).exists():
            shutil.rmtree(working_dir)


def parse_composition_results(comp_file):
    """
    Parse composition analysis results.

    Args:
        comp_file (str): Path to composition output file

    Returns:
        dict: Parsed composition data
    """
    results = {}
    current_id = None

    try:
        with open(comp_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    current_id = line[1:]
                    results[current_id] = {}
                elif line and current_id:
                    # Parse composition data
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            key = parts[0]
                            value = float(parts[1])
                            results[current_id][key] = value
                        except ValueError:
                            continue

    except Exception as e:
        print(f"Error parsing composition file: {e}")
        return {}

    return results


def calculate_basic_properties(sequence):
    """
    Calculate basic sequence properties.

    Args:
        sequence (str): Protein sequence

    Returns:
        dict: Basic properties
    """
    # Amino acid counts
    aa_counts = {}
    for aa in sequence.upper():
        if aa.isalpha():
            aa_counts[aa] = aa_counts.get(aa, 0) + 1

    length = len(sequence)

    # Calculate percentages
    aa_percentages = {aa: count/length * 100 for aa, count in aa_counts.items()}

    # Hydrophobic residues
    hydrophobic = 'AILMFPWV'
    hydrophobic_count = sum(aa_counts.get(aa, 0) for aa in hydrophobic)
    hydrophobic_pct = hydrophobic_count / length * 100

    # Charged residues
    positive = 'KR'
    negative = 'DE'
    positive_count = sum(aa_counts.get(aa, 0) for aa in positive)
    negative_count = sum(aa_counts.get(aa, 0) for aa in negative)
    net_charge = positive_count - negative_count

    return {
        'length': length,
        'aa_counts': aa_counts,
        'aa_percentages': aa_percentages,
        'hydrophobic_percentage': hydrophobic_pct,
        'positive_charges': positive_count,
        'negative_charges': negative_count,
        'net_charge': net_charge
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze protein sequence composition and properties",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze from FASTA file
  python use_case_2_sequence_analysis.py --input examples/data/example.fasta

  # Analyze single sequence
  python use_case_2_sequence_analysis.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein"

Output:
  PREFIX_composition_analysis.txt - Detailed amino acid composition analysis
  PREFIX_properties_analysis.txt  - Physicochemical properties analysis

The analysis provides:
  - Amino acid composition percentages
  - Hydrophobicity analysis
  - Charge distribution
  - Secondary structure propensities
  - Various physicochemical features
        """)

    parser.add_argument("--input", "-i",
                       help="Input FASTA file containing protein sequences")
    parser.add_argument("--sequence", "-s",
                       help="Single protein sequence to analyze")
    parser.add_argument("--id", default="UserSequence",
                       help="Identifier for single sequence (default: UserSequence)")
    parser.add_argument("--output", "-o",
                       help="Output prefix for result files")
    parser.add_argument("--basic-only", action="store_true",
                       help="Show only basic properties without running Perl pipeline")

    args = parser.parse_args()

    # Validate input
    if not args.input and not args.sequence:
        print("Error: Must provide either --input file or --sequence")
        sys.exit(1)

    if args.input and args.sequence:
        print("Error: Cannot specify both --input and --sequence")
        sys.exit(1)

    # Prepare input
    if args.sequence:
        # Validate sequence
        if not re.match(r'^[ACDEFGHIKLMNPQRSTVWY]+$', args.sequence.upper()):
            print("Error: Invalid amino acid sequence")
            sys.exit(1)

        # Create temporary FASTA file
        temp_fasta = tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False)
        write_fasta(args.sequence, args.id, temp_fasta.name)
        temp_fasta.close()
        input_file = temp_fasta.name
        cleanup_temp = True
    else:
        if not Path(args.input).exists():
            print(f"Error: Input file {args.input} not found")
            sys.exit(1)
        input_file = args.input
        cleanup_temp = False

    try:
        output_prefix = args.output or (args.id if args.sequence else Path(input_file).stem)

        # Basic properties for single sequence
        if args.sequence:
            print(f"Basic properties for sequence '{args.id}':")
            props = calculate_basic_properties(args.sequence)
            print(f"Length: {props['length']} amino acids")
            print(f"Hydrophobic residues: {props['hydrophobic_percentage']:.1f}%")
            print(f"Positive charges: {props['positive_charges']}")
            print(f"Negative charges: {props['negative_charges']}")
            print(f"Net charge: {props['net_charge']:+d}")
            print(f"Most common AA: {max(props['aa_counts'], key=props['aa_counts'].get) if props['aa_counts'] else 'N/A'}")

        # Run detailed analysis unless basic-only
        if not args.basic_only:
            output_files = analyze_sequence_composition(input_file, output_prefix)

            if output_files:
                print(f"\nDetailed analysis completed!")
                print(f"Output files:")
                for file_type, path in output_files.items():
                    print(f"  {file_type}: {path}")

                # Parse and show summary
                if 'composition' in output_files:
                    comp_data = parse_composition_results(output_files['composition'])
                    if comp_data:
                        print(f"\nComposition summary:")
                        for seq_id, data in comp_data.items():
                            print(f"  {seq_id}: {len(data)} features analyzed")
            else:
                print("Analysis failed")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    finally:
        if cleanup_temp and 'temp_fasta' in locals():
            os.unlink(temp_fasta.name)


if __name__ == "__main__":
    main()