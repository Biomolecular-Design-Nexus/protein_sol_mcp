"""
Protein solubility prediction utilities.

Core functions for running the protein-sol Perl pipeline with minimal dependencies.
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Union


def get_repo_path() -> Path:
    """Get the path to the protein-sol repository."""
    script_dir = Path(__file__).parent.parent.parent
    repo_dir = script_dir / "repo" / "protein-sol"

    if not repo_dir.exists():
        raise FileNotFoundError(f"Protein-sol repository not found at {repo_dir}")

    return repo_dir


def run_protein_sol_prediction(
    input_fasta: Union[str, Path],
    output_prefix: Optional[str] = None,
    working_dir: Optional[str] = None,
    cleanup: bool = True
) -> Dict[str, str]:
    """
    Run protein solubility prediction using the Perl pipeline.

    Args:
        input_fasta: Path to input FASTA file
        output_prefix: Optional output prefix. If None, uses input filename
        working_dir: Optional working directory. If None, uses temp directory
        cleanup: Whether to cleanup temporary files

    Returns:
        Dictionary containing paths to output files
    """
    if output_prefix is None:
        output_prefix = Path(input_fasta).stem

    repo_dir = get_repo_path()

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

        # Copy input file to working directory
        input_file = Path(working_dir) / "input.fasta"
        shutil.copy2(input_fasta, input_file)

        # Make wrapper script executable
        wrapper_script = Path(working_dir) / "multiple_prediction_wrapper_export.sh"
        wrapper_script.chmod(0o755)

        # Run prediction
        cmd = ["bash", "multiple_prediction_wrapper_export.sh", "input.fasta"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Prediction failed: {result.stderr}")

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
        if cleanup and temp_dir and Path(working_dir).exists():
            shutil.rmtree(working_dir)


def run_composition_analysis(
    input_fasta: Union[str, Path],
    output_prefix: Optional[str] = None
) -> Dict[str, str]:
    """
    Analyze sequence composition and properties.

    Args:
        input_fasta: Path to input FASTA file
        output_prefix: Output prefix for files

    Returns:
        Dictionary with analysis results and output files
    """
    if output_prefix is None:
        output_prefix = Path(input_fasta).stem

    repo_dir = get_repo_path()

    # Use temporary directory for processing
    with tempfile.TemporaryDirectory(prefix="protein_comp_") as working_dir:
        # Copy required files
        required_files = [
            "seq_compositions_perc_pipeline_export.pl",
            "seq_props_ALL_export.pl",
            "seq_reference_data.txt"
        ]

        for file in required_files:
            src = repo_dir / file
            dst = Path(working_dir) / file
            if src.exists():
                shutil.copy2(src, dst)

        # Copy input file
        input_file = Path(working_dir) / "input.fasta"
        shutil.copy2(input_fasta, input_file)

        # Run composition analysis
        cmd = ["perl", "seq_compositions_perc_pipeline_export.pl", "input.fasta"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Composition analysis failed: {result.stderr}")

        # Run properties analysis
        cmd = ["perl", "seq_props_ALL_export.pl", "input.fasta"]
        result = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Properties analysis failed: {result.stderr}")

        # Collect outputs
        output_files = {}

        composition_file = Path(working_dir) / "seq_composition.txt"
        properties_file = Path(working_dir) / "seq_prediction.txt"

        if composition_file.exists():
            final_comp = f"{output_prefix}_composition_analysis.txt"
            shutil.copy2(composition_file, final_comp)
            output_files['composition'] = final_comp

        if properties_file.exists():
            final_props = f"{output_prefix}_properties_analysis.txt"
            shutil.copy2(properties_file, final_props)
            output_files['properties'] = final_props

        return output_files