# protein-sol MCP

> Comprehensive protein solubility prediction and sequence analysis through Model Context Protocol

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The protein-sol MCP server provides comprehensive protein solubility prediction and sequence analysis capabilities based on the University of Manchester protein-sol pipeline. It implements the research by Hebditch et al (2017) Bioinformatics 33:3098-3100, offering both quick analysis tools and scalable batch processing through the Model Context Protocol.

### Features
- **Protein solubility prediction** from amino acid sequences using machine learning models
- **Sequence composition analysis** with physicochemical property calculations
- **Batch processing** of multiple FASTA files with parallel execution
- **Real-time job management** for long-running tasks with progress tracking
- **Dual API design** with synchronous (immediate) and asynchronous (submit) operations

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment (Python 3.10.19)
├── src/
│   ├── server.py           # MCP server entry point
│   ├── jobs/               # Job management system
│   └── tools/              # Tool organization
├── scripts/
│   ├── predict_solubility.py  # Solubility prediction wrapper
│   ├── analyze_sequence.py    # Sequence analysis wrapper
│   ├── batch_predict.py       # Batch processing wrapper
│   └── lib/                    # Shared utilities
├── examples/
│   └── data/               # Demo FASTA files and results
├── configs/                # JSON configuration templates
├── jobs/                   # Job execution workspace (created at runtime)
└── repo/                   # Original protein-sol Perl pipeline
```

---

## Installation

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- Perl 5.x (system-provided, for underlying calculations)

### Create Environment
Please follow the procedure from `reports/step3_environment.md` to setup the environment. The verified workflow is shown below:

```bash
# Navigate to the MCP directory
cd /home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/protein_sol_mcp

# Determine package manager (prefer mamba over conda)
if command -v mamba &> /dev/null; then
    PKG_MGR="mamba"
else
    PKG_MGR="conda"
fi
echo "Using package manager: $PKG_MGR"

# Create conda environment with Python 3.10 and pandas
mamba create -p ./env python=3.10 pandas -y
# or: conda create -p ./env python=3.10 pandas -y

# Activate environment
mamba activate ./env
# or: conda activate ./env

# Install MCP dependencies
pip install fastmcp loguru

# Verify Perl is available
perl --version
```

**Verification Commands:**
```bash
# Test Python environment
mamba run -p ./env python --version  # Should show 3.10.19

# Test core imports
mamba run -p ./env python -c "import pandas, fastmcp; print('✅ Environment ready')"

# Test Perl pipeline
perl repo/protein-sol/server_prediction_seq_export.pl
```

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/predict_solubility.py` | Predict protein solubility from FASTA | See below |
| `scripts/analyze_sequence.py` | Analyze sequence composition and properties | See below |
| `scripts/batch_predict.py` | Process multiple files in parallel | See below |

### Script Examples

#### Protein Solubility Prediction

```bash
# Activate environment
mamba activate ./env

# Basic prediction with show results
python scripts/predict_solubility.py \
  --input examples/data/example.fasta \
  --output my_results \
  --show-results

# Quick prediction without output display
python scripts/predict_solubility.py \
  --input examples/data/small_test.fasta
```

**Parameters:**
- `--input, -i`: Path to input FASTA file (required)
- `--output, -o`: Output file prefix (default: based on input filename)
- `--show-results`: Display prediction summary in terminal (optional)

**Expected Output:**
- `{prefix}_solubility_results.csv` - Main prediction results with percentages
- `{prefix}_detailed_prediction.txt` - 35 sequence features and profiles
- `{prefix}_composition.txt` - Amino acid composition analysis
- `{prefix}_prediction.log` - Processing logs and diagnostics

#### Sequence Analysis

```bash
# Basic analysis (fast, no external dependencies)
python scripts/analyze_sequence.py \
  --sequence "MVKVYAPASSANMSVGFDVL" \
  --id "MyProtein" \
  --basic-only

# Full analysis of FASTA file (requires Perl pipeline)
python scripts/analyze_sequence.py \
  --input examples/data/example.fasta \
  --output detailed_analysis

# Single sequence full analysis
python scripts/analyze_sequence.py \
  --sequence "MKALIVLGLVLLSVTVQGKVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAGDRSTDYGIFQINSRYWCNDGKTPGAVNACHLSCSALLQDNIADAVACAKRVVRDPQGIRAWVAWRNRCQNRDVRQYVQGCGV" \
  --id "LYSC_HUMAN"
```

**Parameters:**
- `--input, -i`: Path to input FASTA file (alternative to sequence)
- `--sequence, -s`: Single protein sequence string (alternative to input)
- `--id`: Sequence identifier for single sequence (required with --sequence)
- `--output, -o`: Output file prefix (optional)
- `--basic-only`: Fast analysis without external dependencies (optional)

#### Batch Processing

```bash
# Process all FASTA files in a directory
python scripts/batch_predict.py \
  --input examples/data/ \
  --output batch_results \
  --workers 4

# Process specific files
python scripts/batch_predict.py \
  --files examples/data/example.fasta examples/data/small_test.fasta \
  --workers 2
```

**Parameters:**
- `--input, -i`: Directory containing FASTA files (alternative to --files)
- `--files`: List of specific FASTA files to process (alternative to --input)
- `--output, -o`: Output directory for results (default: batch_results/)
- `--workers, -w`: Number of parallel workers (default: 2)

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name protein-sol
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add protein-sol -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
# Should show: protein-sol: /path/to/env/bin/python /path/to/src/server.py - ✓ Connected
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "protein-sol": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/protein_sol_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/protein_sol_mcp/src/server.py"]
    }
  }
}
```

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from protein-sol?
```

#### Basic Usage
```
Use predict_protein_solubility with input file @examples/data/example.fasta and show_results True
```

#### Sequence Analysis
```
Use analyze_protein_sequence with sequence "MVKVYAPASSANMSVGFDVL" and sequence_id "test_protein"
```

#### With Configuration
```
Predict solubility for @examples/data/small_test.fasta and show me the results
```

#### Long-Running Tasks (Submit API)
```
Submit batch_predict_solubility for all FASTA files in @examples/data/ using 4 workers
Then check the job status and show me the logs
```

#### Batch Processing
```
Process these files in batch using submit_batch_predict_solubility:
- @examples/data/example.fasta
- @examples/data/small_test.fasta
Use 2 workers and track the progress
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/example.fasta` | Reference a specific FASTA file |
| `@configs/predict_solubility_config.json` | Reference a config file |
| `@examples/data/` | Reference the demo data directory |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "protein-sol": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/protein_sol_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/protein_sol_mcp/src/server.py"]
    }
  }
}
```

### Example Prompts

```bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What tools are available from protein-sol?
> Use predict_protein_solubility with file examples/data/example.fasta
> Submit a batch job for examples/data/ directory using submit_batch_predict_solubility
```

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (< 10 minutes):

| Tool | Description | Parameters | Est. Runtime |
|------|-------------|------------|--------------|
| `predict_protein_solubility` | Predict solubility from FASTA | `input_file`, `output_file`, `show_results` | ~30 sec - 2 min |
| `analyze_protein_sequence` | Analyze sequence composition | `input_file`, `sequence`, `sequence_id`, `output_file`, `basic_only` | ~5-30 sec |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking (> 10 minutes):

| Tool | Description | Parameters | Est. Runtime |
|------|-------------|------------|--------------|
| `submit_batch_predict_solubility` | Batch process multiple files | `input_path`, `input_files`, `output_dir`, `max_workers`, `job_name` | >10 min |
| `submit_large_solubility_prediction` | Large-scale prediction | `input_file`, `output_file`, `job_name` | >10 min |
| `submit_full_sequence_analysis` | Full sequence analysis | `input_file`, `sequence`, `sequence_id`, `output_file`, `job_name` | >10 min |

### Job Management Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_job_status` | Check job progress | `job_id` |
| `get_job_result` | Get results when completed | `job_id` |
| `get_job_log` | View execution logs | `job_id`, `tail` |
| `cancel_job` | Cancel running job | `job_id` |
| `list_jobs` | List all jobs | `status` (optional) |

---

## Examples

### Example 1: Quick Protein Analysis

**Goal:** Analyze a protein sequence for basic properties and predict its solubility

**Using Script:**
```bash
# First analyze the sequence composition
python scripts/analyze_sequence.py \
  --sequence "MVKVYAPASSANMSVGFDVL" \
  --id "MyProtein" \
  --basic-only

# Then predict solubility from a FASTA file
python scripts/predict_solubility.py \
  --input examples/data/small_test.fasta \
  --output quick_analysis \
  --show-results
```

**Using MCP (in Claude Code):**
```
First, use analyze_protein_sequence with sequence "MVKVYAPASSANMSVGFDVL" and sequence_id "MyProtein" and basic_only True

Then use predict_protein_solubility with input_file @examples/data/small_test.fasta and show_results True
```

**Expected Output:**
- Basic sequence statistics: length, hydrophobic percentage, charged percentage
- Solubility predictions: percentage solubility, scaled scores, isoelectric point

### Example 2: Comprehensive File Analysis

**Goal:** Perform complete analysis of protein sequences from a FASTA file

**Using Script:**
```bash
# Full sequence analysis with composition details
python scripts/analyze_sequence.py \
  --input examples/data/example.fasta \
  --output comprehensive_analysis

# Solubility prediction with detailed output
python scripts/predict_solubility.py \
  --input examples/data/example.fasta \
  --output detailed_prediction
```

**Using MCP (in Claude Code):**
```
Use analyze_protein_sequence with input_file @examples/data/example.fasta and basic_only False to get full composition analysis

Then use predict_protein_solubility with input_file @examples/data/example.fasta and show_results True
```

**Expected Output:**
- Detailed amino acid composition analysis
- Physicochemical properties profiles
- Solubility predictions with 35 sequence features
- Hydropathy, entropy, and charge profiles

### Example 3: Batch Processing

**Goal:** Process multiple protein files at once with progress tracking

**Using Script:**
```bash
# Process all FASTA files in the examples directory
python scripts/batch_predict.py \
  --input examples/data/ \
  --output batch_results \
  --workers 4
```

**Using MCP (in Claude Code):**
```
Submit batch_predict_solubility with input_path @examples/data/ and max_workers 4

Then use get_job_status to check progress and get_job_log to see the processing details
```

**Expected Output:**
- Individual prediction files for each input FASTA
- Combined CSV with all results
- Processing report with success rates and timing

### Example 4: Long-Running Job Management

**Goal:** Submit a large analysis job and monitor its progress

**Using MCP (in Claude Code):**
```
# Submit a job
Submit large_solubility_prediction with input_file @examples/data/example.fasta and job_name "comprehensive_analysis"

# Monitor progress
Check the job status using get_job_status

# View live logs
Show me the job logs using get_job_log with tail 50

# Get final results when complete
Get the job results using get_job_result
```

**Expected Workflow:**
1. Job submission returns job_id immediately
2. Status check shows: pending → running → completed
3. Live logs show processing progress
4. Final results include all output files and metadata

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With | Content |
|------|-------------|----------|---------|
| `example.fasta` | Original demo with 2 proteins | All prediction tools | P00547, LYSC_HUMAN sequences |
| `small_test.fasta` | Quick test with 2 short proteins | Fast testing | Test_Protein_1, Test_Protein_2 |
| `example.fasta-protein_sol.csv` | Example CSV output | Understanding output format | Prediction results format |
| `example.fasta-protein_sol_prediction.txt` | Example detailed prediction | Understanding detailed output | 35 features, profiles |
| `seq_reference_data.txt` | Reference solubility data | Pipeline validation | Experimental data |
| `ss_propensities.txt` | Secondary structure data | Pipeline dependencies | Structure propensities |

---

## Configuration Files

The `configs/` directory contains configuration templates:

| Config | Description | Parameters |
|--------|-------------|------------|
| `predict_solubility_config.json` | Solubility prediction settings | `show_results`, `cleanup_temp`, `timeout_seconds` |
| `analyze_sequence_config.json` | Sequence analysis settings | `basic_only`, `include_composition`, `molecular_weight_per_aa` |
| `batch_predict_config.json` | Batch processing settings | `max_workers`, `timeout_per_file`, `continue_on_error` |
| `default_config.json` | General settings | `cleanup_temp_files`, `verbose_output`, `min_sequence_length` |

### Config Example

```json
{
  "prediction": {
    "show_results": true,
    "cleanup_temp": true
  },
  "output": {
    "csv_name": "solubility_results.csv"
  },
  "processing": {
    "timeout_seconds": 300
  }
}
```

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
```bash
# Recreate environment
mamba create -p ./env python=3.10 pandas -y
mamba activate ./env
pip install fastmcp loguru
```

**Problem:** Import errors
```bash
# Verify installation
python -c "import pandas, fastmcp; print('✅ All imports working')"

# Test server import
python -c "from src.server import mcp; print('✅ MCP server imports working')"
```

**Problem:** Permission errors
```bash
# Fix environment permissions
chmod -R u+rwx ./env

# Use mamba run as alternative
mamba run -p ./env python scripts/predict_solubility.py --help
```

### MCP Issues

**Problem:** Server not found in Claude Code
```bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove protein-sol
claude mcp add protein-sol -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

**Problem:** Tools not working
```bash
# Test server directly
python -c "
from src.server import mcp
tools = list(mcp.list_tools().keys())
print(f'✅ Found {len(tools)} tools: {tools}')
"
```

**Problem:** Connection issues
```bash
# Check if server starts correctly
PYTHONPATH="./src:./scripts" ./env/bin/python src/server.py

# Test with FastMCP dev mode
fastmcp dev src/server.py
```

### Job Issues

**Problem:** Job stuck in pending
```bash
# Check job directory
ls -la jobs/

# View job details
cat jobs/<job_id>/job.log

# Check job manager status
python -c "
from src.jobs.manager import job_manager
print(job_manager.list_jobs())
"
```

**Problem:** Job failed
```
Use get_job_log with job_id "<job_id>" and tail 100 to see error details
```

**Problem:** Jobs directory permissions
```bash
# Fix permissions
mkdir -p jobs
chmod 755 jobs

# Clear stuck jobs
rm -rf jobs/*
```

### Pipeline Issues

**Problem:** Perl pipeline errors
```bash
# Test Perl availability
perl --version

# Test Perl pipeline directly
cd repo/protein-sol
perl server_prediction_seq_export.pl

# Check required data files
ls -la ss_propensities.txt seq_reference_data.txt
```

**Problem:** Missing output files
```bash
# Check working directory
pwd  # Should be in protein_sol_mcp root

# Verify input file exists
ls -la examples/data/example.fasta

# Test with absolute paths
python scripts/predict_solubility.py --input $(pwd)/examples/data/example.fasta
```

---

## Development

### Running Tests

```bash
# Activate environment
mamba activate ./env

# Run direct tool tests
python tests/test_tools_direct.py

# Run end-to-end scenarios
python tests/test_e2e_scenarios.py

# Run MCP integration tests
python tests/test_mcp_integration.py
```

### Starting Dev Server

```bash
# Run MCP server in dev mode
fastmcp dev src/server.py

# Test server health
curl -X POST http://localhost:3000 -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Performance Monitoring

```bash
# Monitor job queue
python -c "
from src.jobs.manager import job_manager
jobs = job_manager.list_jobs()
print(f'Active jobs: {len([j for j in jobs[\"jobs\"] if j[\"status\"] in [\"pending\", \"running\"]])}')
"

# Check disk usage
du -sh jobs/
du -sh examples/data/
```

---

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
- **Memory**: Scales with input file size, typically modest requirements (<100MB)

---

## Dependencies Summary

| Tool | Perl Pipeline | External Files | Network |
|------|---------------|----------------|---------|
| Basic sequence analysis | ❌ No | ❌ No | ❌ No |
| Solubility prediction | ✅ Yes | ✅ Yes | ❌ No |
| Full sequence analysis | ✅ Yes | ✅ Yes | ❌ No |
| Batch processing | ✅ Yes | ✅ Yes | ❌ No |

**Note**: Tools requiring the Perl pipeline need the `repo/protein-sol/` directory with the original protein-sol scripts and data files (`ss_propensities.txt`, `seq_reference_data.txt`).

---

## License

Based on the protein-sol tool from the University of Manchester.

## Credits

Based on [protein-sol](https://github.com/protein-sol/protein-sol) by Hebditch et al.

**Citation**: Hebditch et al (2017) "Protein-Sol: A web tool for predicting protein solubility from sequence" Bioinformatics 33:3098-3100.