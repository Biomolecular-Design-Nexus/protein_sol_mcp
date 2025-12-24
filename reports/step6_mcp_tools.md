# Step 6: MCP Tools Documentation

## Server Information
- **Server Name**: protein-sol
- **Version**: 1.0.0
- **Created Date**: 2025-12-20
- **Server Path**: `src/server.py`
- **FastMCP Version**: 2.14.1

## Job Management Tools

The server provides comprehensive job management for long-running tasks:

| Tool | Description | Args | Returns |
|------|-------------|------|---------|
| `get_job_status` | Check job progress | `job_id: str` | Job status, timestamps, error if failed |
| `get_job_result` | Get completed job results | `job_id: str` | Full job results when completed |
| `get_job_log` | View job execution logs | `job_id: str, tail: int = 50` | Log lines and total count |
| `cancel_job` | Cancel running job | `job_id: str` | Success/error message |
| `list_jobs` | List all jobs | `status: str = None` | List of jobs, optionally filtered by status |

### Job Statuses
- **pending**: Job queued, not yet started
- **running**: Job currently executing
- **completed**: Job finished successfully
- **failed**: Job encountered an error
- **cancelled**: Job was cancelled by user

## Sync Tools (Fast Operations < 10 min)

These tools return results immediately and are suitable for quick operations:

| Tool | Description | Source Script | Est. Runtime |
|------|-------------|---------------|--------------|
| `predict_protein_solubility` | Predict solubility from FASTA | `scripts/predict_solubility.py` | ~30 sec - 2 min |
| `analyze_protein_sequence` | Analyze sequence composition | `scripts/analyze_sequence.py` | ~5-30 sec |

### Tool Details

#### predict_protein_solubility
- **Description**: Predict protein solubility from FASTA sequences using the protein-sol pipeline
- **Source Script**: `scripts/predict_solubility.py`
- **Estimated Runtime**: 30 seconds to 2 minutes
- **Dependencies**: Requires Perl pipeline in repo

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to input FASTA file |
| output_file | str | No | None | Output prefix for result files |
| show_results | bool | No | False | Include results summary in response |

**Returns:**
```json
{
  "status": "success",
  "output_files": {
    "csv": "results_solubility_results.csv",
    "detailed": "results_detailed_prediction.txt",
    "composition": "results_composition.txt",
    "log": "results_prediction.log"
  },
  "summary": [...],  // if show_results=True
  "metadata": {...}
}
```

**Example:**
```
Use predict_protein_solubility with input_file "examples/data/example.fasta" and show_results True
```

---

#### analyze_protein_sequence
- **Description**: Analyze amino acid composition and physicochemical properties
- **Source Script**: `scripts/analyze_sequence.py`
- **Estimated Runtime**: 5-30 seconds
- **Dependencies**: None for basic_only=True, Perl pipeline for full analysis

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | No | None | Path to input FASTA file |
| sequence | str | No | None | Single protein sequence string |
| sequence_id | str | No | None | Identifier for sequence (required with sequence) |
| output_file | str | No | None | Output prefix for result files |
| basic_only | bool | No | True | Fast analysis without external dependencies |

**Returns:**
```json
{
  "status": "success",
  "analysis_results": {
    "basic_stats": {
      "sequence_id": {
        "length": 20,
        "hydrophobic_percent": 60.0,
        "charged_percent": 10.0,
        "polar_percent": 30.0,
        "amino_acid_composition": {...}
      }
    }
  },
  "output_files": {...},  // if basic_only=False
  "metadata": {...}
}
```

**Examples:**
```
# Quick basic analysis
Use analyze_protein_sequence with sequence "MVKVYAPASSANMSVGFDVL" and sequence_id "test_protein"

# Full analysis of FASTA file
Use analyze_protein_sequence with input_file "sequences.fasta" and basic_only False
```

---

## Submit Tools (Long Operations > 10 min)

These tools submit jobs for background processing and return a job_id for tracking:

| Tool | Description | Source Script | Est. Runtime | Batch Support |
|------|-------------|---------------|--------------|---------------|
| `submit_batch_predict_solubility` | Batch process FASTA files | `scripts/batch_predict.py` | >10 min | ✅ Yes |
| `submit_large_solubility_prediction` | Large-scale prediction | `scripts/predict_solubility.py` | >10 min | ❌ No |
| `submit_full_sequence_analysis` | Full sequence analysis | `scripts/analyze_sequence.py` | >10 min | ❌ No |

### Tool Details

#### submit_batch_predict_solubility
- **Description**: Process multiple FASTA files for solubility prediction in parallel
- **Source Script**: `scripts/batch_predict.py`
- **Estimated Runtime**: >10 minutes (depends on file count and size)
- **Supports Batch**: ✅ Yes

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_path | str | No | None | Directory containing FASTA files |
| input_files | List[str] | No | None | List of specific FASTA files |
| output_dir | str | No | None | Directory for output files |
| max_workers | int | No | 2 | Number of parallel workers |
| job_name | str | No | auto | Custom job name for tracking |

**Returns:**
```json
{
  "status": "submitted",
  "job_id": "abc12345",
  "message": "Job submitted. Use get_job_status('abc12345') to check progress."
}
```

**Examples:**
```
# Process all FASTA files in a directory
Use submit_batch_predict_solubility with input_path "data/proteins/" and max_workers 4

# Process specific files
Use submit_batch_predict_solubility with input_files ["seq1.fasta", "seq2.fasta"]
```

---

#### submit_large_solubility_prediction
- **Description**: Submit large-scale protein solubility prediction for background processing
- **Source Script**: `scripts/predict_solubility.py`
- **Estimated Runtime**: Variable (>10 minutes for large files)

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to input FASTA file |
| output_file | str | No | None | Output prefix for result files |
| job_name | str | No | auto | Custom job name for tracking |

**Example:**
```
Submit large_solubility_prediction with input_file "large_dataset.fasta"
```

---

#### submit_full_sequence_analysis
- **Description**: Submit comprehensive sequence analysis using the Perl pipeline
- **Source Script**: `scripts/analyze_sequence.py`
- **Estimated Runtime**: Several minutes (depends on sequence count)

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | No | None | Path to input FASTA file |
| sequence | str | No | None | Single protein sequence string |
| sequence_id | str | No | None | Identifier for sequence (required with sequence) |
| output_file | str | No | None | Output prefix for result files |
| job_name | str | No | auto | Custom job name for tracking |

**Example:**
```
Submit full_sequence_analysis with input_file "sequences.fasta"
```

---

## Workflow Examples

### Quick Analysis (Sync)
```
1. Use analyze_protein_sequence with sequence "MVKVYAPASSANMSVGFDVL" and sequence_id "test"
   → Returns results immediately with basic statistics

2. Use predict_protein_solubility with input_file "examples/data/example.fasta"
   → Returns prediction results in ~30 seconds
```

### Long-Running Task (Submit API)
```
1. Submit: Use submit_batch_predict_solubility with input_path "data/" and max_workers 4
   → Returns: {"job_id": "abc123", "status": "submitted"}

2. Check: Use get_job_status with job_id "abc123"
   → Returns: {"status": "running", "started_at": "...", ...}

3. Monitor: Use get_job_log with job_id "abc123"
   → Returns: {"log_lines": [...], "total_lines": 150}

4. Result: Use get_job_result with job_id "abc123"
   → Returns: {"status": "success", "result": {"summary": {...}, "results": [...]}}
```

### Batch Processing Workflow
```
1. Submit batch job:
   Use submit_batch_predict_solubility with input_files ["file1.fasta", "file2.fasta", "file3.fasta"]

2. Monitor progress:
   Use get_job_status with job_id "xyz789"

3. View live logs:
   Use get_job_log with job_id "xyz789" and tail 100

4. Get final results:
   Use get_job_result with job_id "xyz789"
   → Returns processing summary for all files
```

## Error Handling

All tools return structured error responses:

```json
{
  "status": "error",
  "error": "Descriptive error message"
}
```

Common error scenarios:
- **File not found**: Input FASTA file doesn't exist
- **Invalid input**: Malformed sequence or missing required parameters
- **Job not found**: Invalid job_id provided
- **Job not completed**: Trying to get results from running/failed job
- **Dependency error**: Perl pipeline not available

## Performance Guidelines

### When to Use Sync vs Submit APIs

**Use Sync APIs for:**
- Single sequence analysis (basic_only=True)
- Small FASTA files (<10 sequences)
- Quick validation/testing
- Interactive analysis

**Use Submit APIs for:**
- Large FASTA files (>50 sequences)
- Batch processing multiple files
- Long-running comprehensive analysis
- Background processing while doing other tasks

### Resource Usage

- **Basic sequence analysis**: Minimal CPU, no external dependencies
- **Solubility prediction**: Moderate CPU, requires Perl pipeline
- **Batch processing**: CPU scales with max_workers setting
- **Memory**: Scales with input file size, typically modest requirements

## Dependencies Summary

| Tool | Perl Pipeline | External Files | Network |
|------|---------------|----------------|---------|
| Basic sequence analysis | ❌ No | ❌ No | ❌ No |
| Solubility prediction | ✅ Yes | ✅ Yes | ❌ No |
| Full sequence analysis | ✅ Yes | ✅ Yes | ❌ No |
| Batch processing | ✅ Yes | ✅ Yes | ❌ No |

**Note**: Tools requiring the Perl pipeline need the `repo/protein-sol/` directory with the original protein-sol scripts and data files.