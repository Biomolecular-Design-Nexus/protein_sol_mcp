"""
Model Context Protocol (MCP) for protein_sol_mcp

Comprehensive protein solubility prediction toolkit from the University of Manchester implementing the Hebditch et al (2017) Bioinformatics algorithm. Provides both automated pipeline and step-by-step sequence analysis tools for predicting protein solubility from amino acid sequences.

This MCP Server contains tools extracted from the following tutorial files:
1. protein_sol_solubility_predict_mcp
    - protein_sol_solubility_predict_mcp: Run complete automated protein solubility prediction pipeline
"""

from fastmcp import FastMCP

# Import statements (alphabetical order)
from tools.solubility_predict import protein_sol_solubility_predict_mcp
# Server definition and mounting
mcp = FastMCP(name="protein_sol_mcp")
mcp.mount(protein_sol_solubility_predict_mcp)

if __name__ == "__main__":
    mcp.run()