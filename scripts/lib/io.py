"""
Shared I/O functions for MCP scripts.

These are extracted and simplified from repo code to minimize dependencies.
"""
from pathlib import Path
from typing import Union, Any, List
import json
import pandas as pd


def load_json(file_path: Union[str, Path]) -> dict:
    """Load JSON file."""
    with open(file_path) as f:
        return json.load(f)


def save_json(data: dict, file_path: Union[str, Path]) -> None:
    """Save data to JSON file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def write_fasta(sequence: str, identifier: str, output_file: Union[str, Path]) -> None:
    """
    Write a sequence to a FASTA file.

    Args:
        sequence: Protein sequence
        identifier: Sequence identifier
        output_file: Output FASTA file path
    """
    with open(output_file, 'w') as f:
        f.write(f">{identifier}\n")
        f.write(f"{sequence}\n")


def read_fasta(file_path: Union[str, Path]) -> List[tuple]:
    """
    Read sequences from a FASTA file.

    Args:
        file_path: Path to FASTA file

    Returns:
        List of (identifier, sequence) tuples
    """
    sequences = []
    current_id = None
    current_seq = ""

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if current_id is not None:
                    sequences.append((current_id, current_seq))
                current_id = line[1:]  # Remove '>'
                current_seq = ""
            else:
                current_seq += line

    if current_id is not None:
        sequences.append((current_id, current_seq))

    return sequences


def parse_results_csv(csv_file: Union[str, Path]) -> pd.DataFrame:
    """
    Parse the CSV results file and return a pandas DataFrame.

    Args:
        csv_file: Path to CSV results file

    Returns:
        Parsed results DataFrame
    """
    try:
        return pd.read_csv(csv_file)
    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {e}")


def find_fasta_files(input_path: Union[str, Path]) -> List[str]:
    """
    Find all FASTA files in a directory or return single file.

    Args:
        input_path: Path to file or directory

    Returns:
        List of FASTA file paths
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