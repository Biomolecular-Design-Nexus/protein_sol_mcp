# Protein Solubility MCP Server

MCP Server for protein solubility prediction from sequence data using protein-sol.

**Reference**: Hebditch et al (2017) Bioinformatics 33:3098-3100

## Overview

This server provides 5 tools for predicting protein solubility from FASTA sequences using a comprehensive pipeline that includes:

1. **FASTA Reformatting** - Validate and clean sequences
2. **Composition Analysis** - Calculate 36 features (amino acid percentages, charge properties, pI, hydropathy, disorder propensity, entropy)
3. **Solubility Prediction** - Apply weighted linear model based on cell-free expression data
4. **Property Calculation** - Sliding window analysis for disorder, charge, hydropathy profiles
5. **Profile Gathering** - Aggregate windowed profiles with predictions


## Installation

```bash
# Create and activate virtual environment
mamba env create -p ./env python=3.10 pip -y
mamba activate ./env

pip install pandas loguru biopython matplotlib
pip install --ignore-installed fastmcp
```

## Local usage
### 1. Protein solubility prediction

## MCP Usage

### Install ProteinSol MCP Server
```shell
fastmcp install claude-code mcp-servers/protein_sol_mcp/src/protein_sol_mcp.py --python mcp-servers/protein_sol_mcp/env/bin/python
fastmcp install gemini-cli mcp-servers/protein_sol_mcp/src/protein_sol_mcp.py --python mcp-servers/protein_sol_mcp/env/bin/python
```

### Call ProteinSol MCP service
1. Predict protein solubility with Protein-Sol

2. Analyze the regions of soubility propensity
