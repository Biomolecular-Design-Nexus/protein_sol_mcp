"""
Protein solubility prediction tool using protein-sol pipeline.
"""

import csv
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from fastmcp import FastMCP

# Create the MCP instance for solubility prediction tools
protein_sol_solubility_predict_mcp = FastMCP("protein_sol_solubility_predict")


@protein_sol_solubility_predict_mcp.tool()
async def protein_sol_solubility_predict(
    sequence: Optional[str] = None,
    fasta_file: Optional[str] = None,
    csv_file: Optional[str] = None,
    sequence_column: str = "sequence",
    id_column: Optional[str] = None,
    sequence_id: str = "protein",
    quiet: bool = False
) -> Dict:
    """
    Run complete automated protein solubility prediction pipeline.

    Predicts protein solubility using the Hebditch et al (2017) algorithm from
    the University of Manchester. Analyzes amino acid sequences to predict
    solubility metrics including percent-soluble, scaled-soluble, population-soluble,
    and isoelectric point (pI).

    Args:
        sequence: Protein sequence string (amino acids). If provided, a temporary
                 FASTA file will be created. Mutually exclusive with fasta_file and csv_file.
        fasta_file: Path to input FASTA file. Mutually exclusive with sequence and csv_file.
        csv_file: Path to CSV file containing sequences. The CSV will be copied and
                 prediction columns will be appended. Output saved as *.csv_protein_sol.csv.
                 Mutually exclusive with sequence and fasta_file.
        sequence_column: Name of the column containing sequences in CSV file (default: "sequence").
                        Only used when csv_file is provided.
        id_column: Name of the column containing sequence IDs in CSV file (optional).
                  If not provided, row indices will be used as IDs. Only used when csv_file is provided.
        sequence_id: ID to use for the sequence when creating temporary FASTA
                    (default: "protein"). Only used if sequence is provided.
        quiet: Suppress detailed console output (default: False)

    Returns:
        Dictionary containing:
            - success: Boolean indicating if prediction succeeded
            - predictions: List of prediction dictionaries with fields:
                - ID: Sequence identifier
                - sequence: Amino acid sequence
                - percent_sol: Percentage solubility prediction
                - scaled_sol: Scaled solubility score
                - population_sol: Population average solubility
                - pI: Isoelectric point
            - output_files: Dictionary of generated file paths:
                - csv: CSV file with all results (for csv_file input, this is the augmented CSV)
                - prediction: Main prediction results file
                - composition: Sequence composition data file
                - log: Execution log file
            - error: Error message if prediction failed

    Example:
        # Using a sequence string
        result = await protein_sol_solubility_predict(
            sequence="MKLLLLLLLLLLLLLLLLLLLLLLLLLLLL",
            sequence_id="test_protein"
        )

        # Using a FASTA file
        result = await protein_sol_solubility_predict(
            fasta_file="input.fasta"
        )

        # Using a CSV file
        result = await protein_sol_solubility_predict(
            csv_file="proteins.csv",
            sequence_column="protein_seq",
            id_column="protein_id"
        )

    Raises:
        ValueError: If none or multiple input types are provided
    """
    # Validation
    inputs_provided = sum([sequence is not None, fasta_file is not None, csv_file is not None])
    if inputs_provided == 0:
        raise ValueError("One of 'sequence', 'fasta_file', or 'csv_file' must be provided")

    if inputs_provided > 1:
        raise ValueError("Provide only one of 'sequence', 'fasta_file', or 'csv_file'")

    # Get the script path
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "protein_sol_predict.py"
    if not script_path.exists():
        return {
            "success": False,
            "error": f"Prediction script not found at {script_path}"
        }

    temp_fasta = None
    input_fasta = fasta_file
    is_csv_input = csv_file is not None
    csv_data = None

    try:
        # Handle CSV file input
        if csv_file is not None:
            csv_path = Path(csv_file)
            if not csv_path.exists():
                return {
                    "success": False,
                    "error": f"CSV file not found: {csv_file}"
                }

            # Read CSV file
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            # Validate sequence column exists
            if not csv_data:
                return {
                    "success": False,
                    "error": "CSV file is empty"
                }

            if sequence_column not in csv_data[0]:
                return {
                    "success": False,
                    "error": f"Column '{sequence_column}' not found in CSV. Available columns: {', '.join(csv_data[0].keys())}"
                }

            # Validate id_column if specified
            if id_column and id_column not in csv_data[0]:
                return {
                    "success": False,
                    "error": f"Column '{id_column}' not found in CSV. Available columns: {', '.join(csv_data[0].keys())}"
                }

            # Create temporary FASTA file from CSV sequences
            temp_fasta = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.fasta',
                delete=False
            )

            for idx, row in enumerate(csv_data):
                seq = row[sequence_column]
                if not seq or seq.strip() == '':
                    continue

                # Use id_column if specified, otherwise use row index
                seq_id = row[id_column] if id_column else f"row_{idx}"
                temp_fasta.write(f">{seq_id}\n")
                temp_fasta.write(f"{seq.strip()}\n")

            temp_fasta.close()
            input_fasta = temp_fasta.name

        # Create temporary FASTA file if sequence provided
        elif sequence is not None:
            temp_fasta = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.fasta',
                delete=False
            )
            temp_fasta.write(f">{sequence_id}\n")
            temp_fasta.write(f"{sequence}\n")
            temp_fasta.close()
            input_fasta = temp_fasta.name

        # Validate input FASTA exists
        if not Path(input_fasta).exists():
            return {
                "success": False,
                "error": f"Input FASTA file not found: {input_fasta}"
            }

        # Build command
        cmd = ["python3", str(script_path), input_fasta]
        if quiet:
            cmd.append("--quiet")

        # Run the prediction script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Prediction failed with exit code {result.returncode}",
                "stderr": result.stderr,
                "stdout": result.stdout
            }

        # Parse results from the generated CSV file
        input_path = Path(input_fasta)
        output_dir = input_path.parent
        prediction_csv = output_dir / f"{input_path.name}-protein_sol.csv"
        prediction_file = output_dir / f"{input_path.name}-protein_sol_prediction.txt"
        composition_file = output_dir / f"{input_path.name}-protein_sol_composition.txt"
        log_file = output_dir / f"{input_path.name}-protein_sol.log"

        predictions = []
        prediction_dict = {}

        if prediction_csv.exists():
            with open(prediction_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pred = {
                        "ID": row["ID"],
                        "sequence": row["sequence"],
                        "percent_sol": row["percent-sol"],
                        "scaled_sol": row["scaled-sol"],
                        "population_sol": row["population-sol"],
                        "pI": row["pI"]
                    }
                    predictions.append(pred)
                    prediction_dict[row["ID"]] = pred

        # Handle CSV input: create augmented CSV
        output_csv_path = prediction_csv
        if is_csv_input and csv_data:
            csv_input_path = Path(csv_file)
            augmented_csv_path = csv_input_path.parent / f"{csv_input_path.name}_protein_sol.csv"

            # Get original CSV headers
            original_headers = list(csv_data[0].keys())
            new_headers = original_headers + ['percent-sol', 'scaled-sol', 'population-sol', 'pI']

            # Write augmented CSV
            with open(augmented_csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=new_headers)
                writer.writeheader()

                for idx, row in enumerate(csv_data):
                    # Get the ID that was used in the FASTA
                    seq_id = row[id_column] if id_column else f"row_{idx}"

                    # Copy original row data
                    new_row = row.copy()

                    # Add prediction data if available
                    if seq_id in prediction_dict:
                        pred = prediction_dict[seq_id]
                        new_row['percent-sol'] = pred['percent_sol']
                        new_row['scaled-sol'] = pred['scaled_sol']
                        new_row['population-sol'] = pred['population_sol']
                        new_row['pI'] = pred['pI']
                    else:
                        # No prediction found (e.g., empty sequence)
                        new_row['percent-sol'] = ''
                        new_row['scaled-sol'] = ''
                        new_row['population-sol'] = ''
                        new_row['pI'] = ''

                    writer.writerow(new_row)

            output_csv_path = augmented_csv_path

        return {
            "success": True,
            "predictions": predictions,
            "output_files": {
                "csv": str(output_csv_path) if output_csv_path.exists() else None,
                "prediction": str(prediction_file) if prediction_file.exists() else None,
                "composition": str(composition_file) if composition_file.exists() else None,
                "log": str(log_file) if log_file.exists() else None
            },
            "stdout": result.stdout if not quiet else None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

    finally:
        # Clean up temporary FASTA file
        if temp_fasta is not None:
            try:
                Path(temp_fasta.name).unlink()
            except Exception:
                pass
