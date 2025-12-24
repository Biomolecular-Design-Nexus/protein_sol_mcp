# Protein Solubility MCP - Examples and Demo Data

This directory contains example scripts and demo data for the Protein Solubility MCP tool.

## Use Case Scripts

### 1. `use_case_1_predict_solubility.py`
**Description**: Main protein solubility prediction tool
**Complexity**: Medium
**Priority**: High

Predicts protein solubility from amino acid sequences using the University of Manchester protein-sol pipeline.

**Usage:**
```bash
python use_case_1_predict_solubility.py --input examples/data/example.fasta
python use_case_1_predict_solubility.py --input examples/data/small_test.fasta --output test_results
```

**Inputs:**
- FASTA file with protein sequences

**Outputs:**
- `PREFIX_solubility_results.csv` - Main prediction results
- `PREFIX_detailed_prediction.txt` - Detailed analysis with all features
- `PREFIX_composition.txt` - Amino acid composition analysis
- `PREFIX_prediction.log` - Processing log

### 2. `use_case_2_sequence_analysis.py`
**Description**: Protein sequence composition and properties analysis
**Complexity**: Medium
**Priority**: Medium

Analyzes amino acid composition and physicochemical properties of protein sequences.

**Usage:**
```bash
python use_case_2_sequence_analysis.py --input examples/data/example.fasta
python use_case_2_sequence_analysis.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein"
python use_case_2_sequence_analysis.py --sequence "MVKVYAPASSANMSVGFDVL" --basic-only
```

**Inputs:**
- FASTA file or single sequence string

**Outputs:**
- `PREFIX_composition_analysis.txt` - Detailed composition analysis
- `PREFIX_properties_analysis.txt` - Physicochemical properties

### 3. `use_case_3_batch_prediction.py`
**Description**: Batch processing for multiple FASTA files
**Complexity**: Complex
**Priority**: Medium

Processes multiple FASTA files in parallel for high-throughput solubility prediction.

**Usage:**
```bash
python use_case_3_batch_prediction.py --input examples/data/
python use_case_3_batch_prediction.py --files file1.fasta file2.fasta --workers 4
```

**Inputs:**
- Directory with FASTA files or list of specific files

**Outputs:**
- Individual result files for each input
- `combined_solubility_results.csv` - All results combined
- `batch_processing_report.txt` - Processing summary

## Demo Data

### Input Files
- `example.fasta` - Original example from protein-sol repository (2 proteins)
- `small_test.fasta` - Additional test file with short protein sequences
- `ss_propensities.txt` - Secondary structure propensities data
- `seq_reference_data.txt` - Reference data for solubility predictions

### Example Output Files
- `example.fasta-protein_sol.csv` - Example CSV output
- `example.fasta-protein_sol_prediction.txt` - Example detailed prediction
- `example.fasta-protein_sol_composition.txt` - Example composition analysis
- `example.fasta-protein_sol.log` - Example processing log

## Testing the Examples

### Quick Test
```bash
# Test basic solubility prediction
python use_case_1_predict_solubility.py --input examples/data/small_test.fasta

# Test sequence analysis
python use_case_2_sequence_analysis.py --input examples/data/small_test.fasta

# Test with single sequence
python use_case_2_sequence_analysis.py --sequence "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEAEMKASED" --id "TestProtein"
```

### Batch Processing Test
```bash
# Process all files in data directory
python use_case_3_batch_prediction.py --input examples/data/ --output test_batch
```

## Expected Results

### Solubility Prediction Output
The main CSV output contains:
- `ID` - Protein identifier from FASTA
- `sequence` - Protein sequence
- `percent-sol` - Percentage solubility prediction (0-100%)
- `scaled-sol` - Scaled solubility score (0-1)
- `population-sol` - Population-based solubility estimate
- `pI` - Isoelectric point

### Analysis Features
The detailed prediction includes:
- 35 sequence features calculated over 21-amino-acid windows
- Amino acid composition percentages
- Kyte-Doolittle hydropathy profiles
- Uversky fold index profiles
- Sequence entropy profiles
- Net charge profiles
- Secondary structure propensities

## Requirements

These scripts require:
- Python 3.10+
- pandas
- Perl 5.x (for running the underlying protein-sol pipeline)
- The protein-sol repository files (automatically handled)

## Environment Setup

Make sure to activate the conda environment before running:
```bash
mamba activate ./env
# or
conda activate ./env
```

All scripts are designed to work with relative paths from the MCP root directory.