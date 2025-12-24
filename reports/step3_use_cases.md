# Step 3: Use Cases Report

## Scan Information
- **Scan Date**: 2024-12-19
- **Filter Applied**: None
- **Repository Type**: Perl-based protein solubility prediction pipeline
- **Environment Strategy**: Single Python environment for MCP + system Perl

## Use Cases

### UC-001: Protein Solubility Prediction
- **Description**: Predict protein solubility from amino acid sequences using the protein-sol pipeline
- **Script Path**: `examples/use_case_1_predict_solubility.py`
- **Complexity**: Medium
- **Priority**: High
- **Environment**: `./env`
- **Source**: `repo/protein-sol/multiple_prediction_wrapper_export.sh`, README_sequence_prediction.txt

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| input_fasta | file | Input FASTA file with protein sequences | --input, -i |
| output_prefix | string | Optional output file prefix | --output, -o |
| working_dir | string | Optional working directory | --working-dir |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| csv_results | file | Main prediction results (CSV format) |
| detailed_prediction | file | Detailed analysis with all features |
| composition_analysis | file | Amino acid composition analysis |
| processing_log | file | Processing log and diagnostics |

**Example Usage:**
```bash
python examples/use_case_1_predict_solubility.py --input examples/data/example.fasta --output my_results
python examples/use_case_1_predict_solubility.py --input examples/data/small_test.fasta --show-results
```

**Example Data**: `examples/data/example.fasta`, `examples/data/small_test.fasta`

---

### UC-002: Sequence Composition Analysis
- **Description**: Analyze amino acid composition and physicochemical properties of protein sequences
- **Script Path**: `examples/use_case_2_sequence_analysis.py`
- **Complexity**: Medium
- **Priority**: Medium
- **Environment**: `./env`
- **Source**: `repo/protein-sol/seq_compositions_perc_pipeline_export.pl`, `seq_props_ALL_export.pl`

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| input_fasta | file | Input FASTA file | --input, -i |
| sequence | string | Single protein sequence | --sequence, -s |
| identifier | string | Sequence identifier for single sequence | --id |
| basic_only | flag | Show only basic properties | --basic-only |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| composition_analysis | file | Detailed amino acid composition |
| properties_analysis | file | Physicochemical properties |
| basic_summary | stdout | Basic sequence properties |

**Example Usage:**
```bash
python examples/use_case_2_sequence_analysis.py --input examples/data/example.fasta
python examples/use_case_2_sequence_analysis.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein"
python examples/use_case_2_sequence_analysis.py --sequence "MVLSEGEWQL" --basic-only
```

**Example Data**: `examples/data/example.fasta`, `examples/data/small_test.fasta`

---

### UC-003: Batch Solubility Prediction
- **Description**: Process multiple FASTA files in parallel for high-throughput solubility prediction
- **Script Path**: `examples/use_case_3_batch_prediction.py`
- **Complexity**: Complex
- **Priority**: Medium
- **Environment**: `./env`
- **Source**: Extension of multiple_prediction_wrapper_export.sh for batch processing

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| input_dir | directory | Directory containing FASTA files | --input, -i |
| file_list | list | Specific FASTA files to process | --files |
| output_dir | directory | Output directory for results | --output, -o |
| workers | integer | Number of parallel workers | --workers, -w |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| individual_results | files | Individual result files per input |
| combined_csv | file | All results combined into single CSV |
| processing_report | file | Batch processing summary |

**Example Usage:**
```bash
python examples/use_case_3_batch_prediction.py --input examples/data/ --output batch_results
python examples/use_case_3_batch_prediction.py --files file1.fasta file2.fasta --workers 4
```

**Example Data**: `examples/data/` (contains multiple FASTA files)

---

## Summary

| Metric | Count |
|--------|-------|
| Total Use Cases Found | 3 |
| Scripts Created | 3 |
| High Priority | 1 |
| Medium Priority | 2 |
| Low Priority | 0 |
| Demo Data Copied | ✅ |
| Perl Pipeline Tested | ✅ |

## Demo Data Index

| Source | Destination | Description |
|--------|-------------|-------------|
| `repo/protein-sol/example.fasta` | `examples/data/example.fasta` | Original example with 2 proteins (P00547, LYSC_HUMAN) |
| `repo/protein-sol/example.fasta-protein_sol.csv` | `examples/data/example.fasta-protein_sol.csv` | Example CSV output |
| `repo/protein-sol/example.fasta-protein_sol_prediction.txt` | `examples/data/example.fasta-protein_sol_prediction.txt` | Example detailed prediction |
| `repo/protein-sol/ss_propensities.txt` | `examples/data/ss_propensities.txt` | Secondary structure propensities data |
| `repo/protein-sol/seq_reference_data.txt` | `examples/data/seq_reference_data.txt` | Reference data for solubility predictions |
| Created | `examples/data/small_test.fasta` | Additional test file with 2 short proteins |

## Technical Analysis

### Perl Pipeline Components
The protein-sol pipeline consists of:
1. **fasta_seq_reformat_export.pl** - FASTA format processing
2. **seq_compositions_perc_pipeline_export.pl** - Amino acid composition analysis
3. **server_prediction_seq_export.pl** - Main solubility prediction
4. **seq_props_ALL_export.pl** - Sequence properties calculation
5. **profiles_gather_export.pl** - Profile data gathering
6. **multiple_prediction_wrapper_export.sh** - Main wrapper script

### Data Requirements
- **ss_propensities.txt** - Secondary structure propensities (1037 bytes)
- **seq_reference_data.txt** - Experimental solubility reference data (4544 bytes)

### Output Format Analysis
The pipeline generates multiple output files:
- **CSV format**: ID, sequence, percent-sol, scaled-sol, population-sol, pI
- **Detailed prediction**: 35 features, profiles for Kyte-Doolittle, Uversky fold index, entropy, charge
- **Composition**: Amino acid percentages and physicochemical properties

### Performance Characteristics
- **Processing time**: ~1-5 seconds per protein (tested with example data)
- **Scalability**: Suitable for batch processing with parallel execution
- **Memory usage**: Low (mostly file-based processing)

## Integration Status

### Perl Pipeline Integration
- [x] All required scripts accessible
- [x] Reference data files present
- [x] Pipeline tested with example data
- [x] Output format understood and documented

### Python Wrapper Status
- [x] Core functionality implemented
- [x] Error handling included
- [x] Command-line interfaces created
- [x] Documentation provided
- [ ] Output file handling needs refinement (file naming issues identified)
- [ ] Full integration testing pending

### MCP Server Readiness
The use cases provide a solid foundation for MCP tool implementation:
1. **Solubility prediction** - Primary MCP function
2. **Sequence analysis** - Supporting analysis capabilities
3. **Batch processing** - High-throughput operations

## Next Steps

1. **Fix output file naming** in Python wrapper scripts
2. **Complete integration testing** of all use cases
3. **Implement MCP server** using the validated use cases
4. **Add error handling** for edge cases and invalid inputs
5. **Performance optimization** for batch operations