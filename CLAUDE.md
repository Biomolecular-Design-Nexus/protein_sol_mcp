# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for protein solubility prediction using the Hebditch et al (2017) algorithm from the University of Manchester protein-sol pipeline. Exposes a single tool (`protein_sol_solubility_predict`) that accepts protein sequences via string, FASTA file, or CSV file.

## Architecture

The server uses **FastMCP** with a mount pattern:

- `src/server.py` — Entry point. Creates the root `FastMCP("protein_sol_mcp")` instance and mounts sub-MCPs.
- `src/tools/solubility_predict.py` — The sole tool implementation. Creates a sub-MCP (`protein_sol_solubility_predict`) that gets mounted into the root server. Handles input validation, temp file creation, subprocess invocation, and result parsing.
- `scripts/protein_sol_predict.py` — Python wrapper that the tool calls via `subprocess.run()`. Parses FASTA, invokes the Perl pipeline for each sequence, and writes output CSVs.
- `scripts/lib/protein_sol.py` — Core utility that locates and runs the Perl pipeline at `repo/protein-sol/`.
- `repo/protein-sol/` — Original Perl pipeline (`server_prediction_seq_export.pl`) with required data files (`ss_propensities.txt`, `seq_reference_data.txt`).
- `src/jobs/manager.py` — Job manager for async/batch tasks (currently unused by the simplified server).

**Data flow:** MCP tool → `subprocess` → `scripts/protein_sol_predict.py` → Perl pipeline → CSV/TXT output files → parsed back into tool response dict.

## Commands

```bash
# Environment setup
mamba create -p ./env python=3.10 pandas -y
mamba activate ./env
pip install fastmcp loguru

# Run MCP server
./env/bin/python src/server.py

# Dev mode (with inspector UI)
fastmcp dev src/server.py

# Run prediction script directly
python scripts/protein_sol_predict.py examples/data/example.fasta

# Tests
python tests/test_tools_direct.py
python tests/test_e2e_scenarios.py
python tests/test_mcp_integration.py

# Register with Claude Code
claude mcp add protein_sol_mcp -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

## Key Details

- The conda environment lives at `./env` (local prefix, not named).
- The tool requires **Perl** on the system PATH for the underlying prediction pipeline.
- Output files are written next to the input file: `{input}-protein_sol.csv`, `{input}-protein_sol_prediction.txt`, `{input}-protein_sol_composition.txt`, `{input}-protein_sol.log`.
- For CSV input, an augmented copy is created as `{input}_protein_sol.csv` with prediction columns appended.
- The tool script path is resolved relative to `src/tools/solubility_predict.py` via `Path(__file__).resolve().parent.parent.parent / "scripts"`.
