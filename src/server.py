"""MCP Server for protein-sol

Provides both synchronous and asynchronous (submit) APIs for all tools.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List
import sys

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from loguru import logger

# Create MCP server
mcp = FastMCP("protein-sol")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)

@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)

@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)

@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)

@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)

# ==============================================================================
# Synchronous Tools (for fast operations < 10 min)
# ==============================================================================

@mcp.tool()
def predict_protein_solubility(
    input_file: str,
    output_file: Optional[str] = None,
    show_results: bool = False
) -> dict:
    """
    Predict protein solubility from FASTA sequences.

    This is a synchronous operation that typically takes 30 seconds to a few minutes
    depending on the number of sequences. For large batch processing, use
    submit_batch_predict_solubility instead.

    Args:
        input_file: Path to input FASTA file containing protein sequences
        output_file: Optional output prefix for result files (default: input filename)
        show_results: Whether to include results summary in response

    Returns:
        Dictionary with:
        - output_files: Dict of generated output file paths
        - summary: Results summary if show_results=True
        - metadata: Execution metadata
    """
    # Import the script's main function
    from predict_solubility import run_predict_solubility

    try:
        result = run_predict_solubility(
            input_file=input_file,
            output_file=output_file,
            show_results=show_results
        )

        response = {
            "status": "success",
            "output_files": result["output_files"],
            "metadata": result["metadata"]
        }

        # Include summary if requested and available
        if show_results and result["result"] is not None:
            response["summary"] = result["result"].to_dict('records')

        return response

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {"status": "error", "error": f"File not found: {e}"}
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def analyze_protein_sequence(
    input_file: Optional[str] = None,
    sequence: Optional[str] = None,
    sequence_id: Optional[str] = None,
    output_file: Optional[str] = None,
    basic_only: bool = True
) -> dict:
    """
    Analyze amino acid composition and physicochemical properties of protein sequences.

    This is a fast operation that analyzes sequence composition. Use basic_only=True
    for quick analysis (5-30 seconds) or basic_only=False for full analysis that
    requires the Perl pipeline.

    Args:
        input_file: Path to input FASTA file (alternative to sequence)
        sequence: Single protein sequence string (alternative to input_file)
        sequence_id: Identifier for single sequence (required with sequence)
        output_file: Optional output prefix for result files
        basic_only: If True, performs only basic analysis (faster, no external deps)

    Returns:
        Dictionary with:
        - analysis_results: Basic statistics or full analysis results
        - output_files: Generated output files (if basic_only=False)
        - metadata: Execution metadata

    Examples:
        # Quick basic analysis of a sequence
        analyze_protein_sequence(sequence="MVKVYAPASSANMSVGFDVL", sequence_id="test", basic_only=True)

        # Full analysis of FASTA file
        analyze_protein_sequence(input_file="sequences.fasta", basic_only=False)
    """
    # Import the script's main function
    from analyze_sequence import run_analyze_sequence

    try:
        # Validate inputs
        if sequence and not sequence_id:
            return {"status": "error", "error": "sequence_id is required when using sequence"}

        if not input_file and not sequence:
            return {"status": "error", "error": "Either input_file or sequence must be provided"}

        result = run_analyze_sequence(
            input_file=input_file,
            sequence=sequence,
            sequence_id=sequence_id,
            output_file=output_file,
            basic_only=basic_only
        )

        return {
            "status": "success",
            "analysis_results": result["result"],
            "output_files": result.get("output_files", {}),
            "metadata": result["metadata"]
        }

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {"status": "error", "error": f"File not found: {e}"}
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Submit Tools (for long-running operations > 10 min)
# ==============================================================================

@mcp.tool()
def submit_batch_predict_solubility(
    input_path: Optional[str] = None,
    input_files: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    max_workers: int = 2,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit batch protein solubility prediction for background processing.

    This operation processes multiple FASTA files in parallel and may take more
    than 10 minutes depending on the number of files. Returns a job_id for tracking.

    Args:
        input_path: Directory containing FASTA files (alternative to input_files)
        input_files: List of specific FASTA files to process (alternative to input_path)
        output_dir: Directory for output files
        max_workers: Number of parallel workers (default: 2)
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results
        - get_job_log(job_id) to see logs

    Examples:
        # Process all FASTA files in a directory
        submit_batch_predict_solubility(input_path="data/proteins/", max_workers=4)

        # Process specific files
        submit_batch_predict_solubility(input_files=["seq1.fasta", "seq2.fasta"])
    """
    script_path = str(SCRIPTS_DIR / "batch_predict.py")

    # Prepare arguments for the batch script
    args = {
        "workers": max_workers
    }

    # Handle input specification
    if input_files:
        # Special handling: pass as files_list for batch script
        args["files_list"] = input_files
    elif input_path:
        args["input"] = input_path
    else:
        return {"status": "error", "error": "Either input_path or input_files must be provided"}

    if output_dir:
        args["output"] = output_dir

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or f"batch_predict_{max_workers}_workers"
    )

@mcp.tool()
def submit_large_solubility_prediction(
    input_file: str,
    output_file: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit large-scale protein solubility prediction for background processing.

    Use this for very large FASTA files or when you want to run prediction
    in the background. For smaller files, use predict_protein_solubility instead.

    Args:
        input_file: Path to input FASTA file
        output_file: Optional output prefix for result files
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id for tracking the job
    """
    script_path = str(SCRIPTS_DIR / "predict_solubility.py")

    args = {
        "input": input_file
    }
    if output_file:
        args["output"] = output_file

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or f"predict_{Path(input_file).stem}"
    )

@mcp.tool()
def submit_full_sequence_analysis(
    input_file: Optional[str] = None,
    sequence: Optional[str] = None,
    sequence_id: Optional[str] = None,
    output_file: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit full sequence analysis for background processing.

    This performs comprehensive sequence analysis using the Perl pipeline,
    which may take several minutes. For quick basic analysis, use
    analyze_protein_sequence with basic_only=True instead.

    Args:
        input_file: Path to input FASTA file (alternative to sequence)
        sequence: Single protein sequence string (alternative to input_file)
        sequence_id: Identifier for single sequence (required with sequence)
        output_file: Optional output prefix for result files
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id for tracking the analysis job
    """
    script_path = str(SCRIPTS_DIR / "analyze_sequence.py")

    args = {}

    # Handle input specification
    if sequence and sequence_id:
        args["sequence"] = sequence
        args["id"] = sequence_id
    elif input_file:
        args["input"] = input_file
    else:
        return {"status": "error", "error": "Either input_file or (sequence + sequence_id) must be provided"}

    if output_file:
        args["output"] = output_file

    # Full analysis (not basic_only)
    # The script will do full analysis by default

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or f"analyze_{sequence_id or Path(input_file or 'sequence').stem}"
    )

# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()