# Protein Solubility MCP Server

MCP Server for protein solubility prediction from sequence data using protein-sol.

**Reference**: Hebditch et al (2017) Bioinformatics 33:3098-3100

## Overview

This server provides a tool for predicting protein solubility from protein sequences using protein-sol:

1. **Solubility Prediction** - Apply weighted linear model based on cell-free expression data

It accepts sequences, fasta, or csv as file input formats.

## Installation

```bash
# Create and activate virtual environment
mamba env create -p ./env python=3.10 pip -y
mamba activate ./env

pip install pandas loguru sniffio
pip install --ignore-installed fastmcp
```

## Local usage
### 1. Protein solubility prediction
```shell
python scripts/protein_sol_predict.py scripts/protein-sol/example.fasta
```
## MCP Usage

### Install ProteinSol MCP Server
```shell
fastmcp install claude-code tool-mcps/protein_sol_mcp/src/protein_sol_mcp.py --python tool-mcps/protein_sol_mcp/env/bin/python
fastmcp install gemini-cli tool-mcps/protein_sol_mcp/src/protein_sol_mcp.py --python tool-mcps/protein_sol_mcp/env/bin/python
```

### Call ProteinSol MCP service
1. Predict protein solubility with Protein-Sol
```markdown
Can you predict the solubility for @examples/case2.1_subtilisin/data.csv  using protein_sol mcp? 

Please convert the relative path to absolution path before calling the MCP servers. 
```