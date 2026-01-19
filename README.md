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
- **Protein solubility prediction** from amino acid sequences using the Hebditch et al (2017) algorithm
- **Flexible input support**: sequence strings, FASTA files, or CSV files
- **Automatic output generation**: CSV results, detailed predictions, composition analysis

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment (Python 3.10.19)
├── src/
│   ├── server.py           # MCP server entry point
│   └── tools/              # Tool implementations
├── scripts/
│   ├── protein_sol_predict.py # Core prediction script
│   └── lib/                    # Shared utilities
├── examples/
│   └── data/               # Demo FASTA files and results
└── repo/                   # Original protein-sol Perl pipeline
```

---

## Installation

### Quick Setup (Recommended)

Run the automated setup script:

```bash
cd protein_sol_mcp
bash quick_setup.sh
```

The script will create the conda environment, install all dependencies, and display the Claude Code configuration. See `quick_setup.sh --help` for options like `--skip-env`.

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- Perl 5.x (system-provided, for underlying calculations)

### Manual Installation (Alternative)

If you prefer manual installation or need to customize the setup, follow `reports/step3_environment.md`:

```bash
# Navigate to the MCP directory
cd /home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/protein_sol_mcp

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

## Local Usage (Script)

You can use the prediction script directly without MCP for local processing.

### Protein Solubility Prediction

```bash
# Activate environment
mamba activate ./env

# Run prediction on a FASTA file
python scripts/protein_sol_predict.py examples/data/example.fasta
```

**Expected Output Files:**
- `{input}-protein_sol.csv` - Main prediction results
- `{input}-protein_sol_prediction.txt` - Detailed prediction with 35 features
- `{input}-protein_sol_composition.txt` - Amino acid composition analysis
- `{input}-protein_sol.log` - Processing logs

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name protein_sol_mcp
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add protein_sol_mcp -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
# Should show: protein_sol_mcp: /path/to/env/bin/python /path/to/src/server.py - ✓ Connected
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "protein_sol_mcp": {
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
What tools are available from protein_sol_mcp?
```

#### Using a Sequence String
```
Use protein_sol_solubility_predict with sequence "MKLLLLLLLLLLLLLLLLLLLLLLLLLLLL" and sequence_id "test_protein"
```

#### Using a FASTA File
```
Use protein_sol_solubility_predict with fasta_file @examples/data/example.fasta
```

#### Using a CSV File
```
Use protein_sol_solubility_predict with csv_file @data/proteins.csv and sequence_column "protein_seq"
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/example.fasta` | Reference a specific FASTA file |
| `@examples/data/small_test.fasta` | Reference demo test file |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "protein_sol_mcp": {
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
> What tools are available from protein_sol_mcp?
> Use protein_sol_solubility_predict with fasta_file examples/data/example.fasta
```

---

## Available Tools

### protein_sol_solubility_predict

Run complete automated protein solubility prediction pipeline using the Hebditch et al (2017) algorithm.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sequence` | string | One of three | Protein sequence string (amino acids) |
| `fasta_file` | string | One of three | Path to input FASTA file |
| `csv_file` | string | One of three | Path to CSV file containing sequences |
| `sequence_column` | string | No | Column name for sequences in CSV (default: "sequence") |
| `id_column` | string | No | Column name for sequence IDs in CSV |
| `sequence_id` | string | No | ID for sequence when using `sequence` parameter (default: "protein") |
| `quiet` | bool | No | Suppress detailed console output (default: False) |

**Input Options** (mutually exclusive - provide exactly one):
- `sequence`: Direct protein sequence string
- `fasta_file`: Path to FASTA file
- `csv_file`: Path to CSV file (will create augmented output with predictions)

**Returns:**

| Field | Description |
|-------|-------------|
| `success` | Boolean indicating if prediction succeeded |
| `predictions` | List of prediction results with ID, sequence, percent_sol, scaled_sol, population_sol, pI |
| `output_files` | Dictionary of generated file paths (csv, prediction, composition, log) |
| `error` | Error message if prediction failed |

---

## Examples

### Example 1: Predict from Sequence String

**Goal:** Predict solubility from a protein sequence

**Using MCP (in Claude Code):**
```
Use protein_sol_solubility_predict with sequence "MKLLLLLLLLLLLLLLLLLLLLLLLLLLLL" and sequence_id "test_protein"
```

**Expected Output:**
- Solubility predictions: percent-sol, scaled-sol, population-sol, pI
- Output files: CSV results, prediction details, composition analysis

### Example 2: Predict from FASTA File

**Goal:** Predict solubility for all sequences in a FASTA file

**Using MCP (in Claude Code):**
```
Use protein_sol_solubility_predict with fasta_file @examples/data/example.fasta
```

**Expected Output:**
- Predictions for each sequence in the FASTA file
- Output files saved alongside input file

### Example 3: Process CSV with Sequences

**Goal:** Add solubility predictions to an existing CSV file

**Using MCP (in Claude Code):**
```
Use protein_sol_solubility_predict with csv_file @data/proteins.csv and sequence_column "protein_seq" and id_column "protein_id"
```

**Expected Output:**
- Original CSV augmented with prediction columns
- Output saved as `{input}_protein_sol.csv`

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
claude mcp remove protein_sol_mcp
claude mcp add protein_sol_mcp -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

**Problem:** Tools not working
```bash
# Test server directly
python -c "
from src.server import mcp
print(f'MCP Name: {mcp.name}')
"
```

**Problem:** Connection issues
```bash
# Check if server starts correctly
./env/bin/python src/server.py

# Test with FastMCP dev mode
fastmcp dev src/server.py
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

---

## Dependencies Summary

| Component | Perl Pipeline | External Files | Network |
|-----------|---------------|----------------|---------|
| `protein_sol_solubility_predict` | Yes | Yes | No |

**Note**: The tool requires the Perl pipeline in `scripts/protein-sol/` directory with data files (`ss_propensities.txt`, `seq_reference_data.txt`).

---

## License

Based on the protein-sol tool from the University of Manchester.

## Credits

Based on [protein-sol](https://github.com/protein-sol/protein-sol) by Hebditch et al.

**Citation**: Hebditch et al (2017) "Protein-Sol: A web tool for predicting protein solubility from sequence" Bioinformatics 33:3098-3100.