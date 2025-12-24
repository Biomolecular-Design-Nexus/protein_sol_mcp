# MCP Scripts

Clean, self-contained scripts extracted from use cases for MCP tool wrapping.

## Design Principles

1. **Minimal Dependencies**: Only essential packages imported (pandas, pathlib, argparse)
2. **Self-Contained**: Common functions moved to shared library (`lib/`)
3. **Configurable**: Parameters in config files, not hardcoded
4. **MCP-Ready**: Each script has a main function ready for MCP wrapping

## Scripts

| Script | Description | Repo Dependent | Config | Status |
|--------|-------------|----------------|--------|--------|
| `predict_solubility.py` | Predict protein solubility from FASTA | Yes (Perl pipeline) | `configs/predict_solubility_config.json` | ✅ Working |
| `analyze_sequence.py` | Analyze sequence composition and properties | Partial (basic mode works) | `configs/analyze_sequence_config.json` | ⚠️ Partial |
| `batch_predict.py` | Batch process multiple FASTA files | Yes (Perl pipeline) | `configs/batch_predict_config.json` | ✅ Working |

## Dependencies

### Essential (Required)
- **pandas**: For CSV parsing and data manipulation
- **pathlib**: For file path handling
- **argparse**: For command line interfaces
- **typing**: For type hints
- **json**: For configuration files

### Standard Library (No install needed)
- os, sys, subprocess, tempfile, shutil, time, re
- concurrent.futures: For parallel processing

### External Dependencies (from repo)
- **Perl pipeline**: `repo/protein-sol/` directory with Perl scripts
- All scripts depend on the protein-sol Perl pipeline being available

## Usage

### Environment Setup
```bash
# Activate the conda/mamba environment
mamba activate ./env  # or: conda activate ./env

# Set Python path to include lib directory
export PYTHONPATH=.
```

### Individual Scripts

#### Predict Solubility
```bash
# Basic prediction
python scripts/predict_solubility.py --input examples/data/example.fasta

# With custom output prefix
python scripts/predict_solubility.py --input input.fasta --output results/my_prediction

# Show results summary
python scripts/predict_solubility.py --input input.fasta --show-results
```

#### Analyze Sequence
```bash
# Analyze FASTA file (full mode - requires Perl pipeline)
python scripts/analyze_sequence.py --input examples/data/example.fasta

# Analyze single sequence (basic mode - works independently)
python scripts/analyze_sequence.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein" --basic-only

# Single sequence with full analysis (requires Perl pipeline)
python scripts/analyze_sequence.py --sequence "MVKVYAPASSANMSVGFDVL" --id "MyProtein"
```

#### Batch Prediction
```bash
# Process directory with 2 workers
python scripts/batch_predict.py --input examples/data/ --workers 2

# Process specific files with custom output directory
python scripts/batch_predict.py --files file1.fasta file2.fasta --output results/ --workers 4
```

### Using Configuration Files
```bash
# Create custom config
cat > my_config.json << EOF
{
  "show_results": true,
  "cleanup_temp": false,
  "max_workers": 4
}
EOF

# Use with script
python scripts/predict_solubility.py --input input.fasta --config my_config.json
```

## Shared Library

Common functions are in `scripts/lib/`:

### `lib/io.py`
- `write_fasta()`: Write sequences to FASTA files
- `read_fasta()`: Read sequences from FASTA files
- `parse_results_csv()`: Parse prediction CSV results
- `find_fasta_files()`: Discover FASTA files in directories
- `load_json()`, `save_json()`: Configuration file handling

### `lib/protein_sol.py`
- `run_protein_sol_prediction()`: Execute Perl pipeline for solubility prediction
- `run_composition_analysis()`: Execute Perl pipeline for composition analysis
- `get_repo_path()`: Get path to protein-sol repository

## For MCP Wrapping (Step 6)

Each script exports a main function that can be wrapped:

```python
# Import the main function
from scripts.predict_solubility import run_predict_solubility
from scripts.analyze_sequence import run_analyze_sequence
from scripts.batch_predict import run_batch_predict

# In MCP tool definition:
@mcp.tool()
def predict_protein_solubility(input_file: str, output_prefix: str = None):
    """Predict protein solubility from FASTA file."""
    result = run_predict_solubility(input_file, output_prefix)
    return {
        "csv_file": result["output_files"].get("csv"),
        "summary": result["result"].to_dict() if result["result"] is not None else None
    }

@mcp.tool()
def analyze_protein_sequence(sequence: str, sequence_id: str):
    """Analyze protein sequence composition and properties."""
    result = run_analyze_sequence(sequence=sequence, sequence_id=sequence_id, basic_only=True)
    return result["result"]["basic_stats"][sequence_id]

@mcp.tool()
def batch_predict_solubility(input_directory: str, max_workers: int = 2):
    """Batch process multiple FASTA files for solubility prediction."""
    result = run_batch_predict(input_path=input_directory, max_workers=max_workers)
    return {
        "summary": result["summary"],
        "report_file": result["report_file"]
    }
```

## Testing

### Basic Functionality Tests
```bash
# Test imports and CLI help
cd scripts
export PYTHONPATH=.

# Test help messages
python predict_solubility.py --help
python analyze_sequence.py --help
python batch_predict.py --help

# Test basic sequence analysis (works without Perl)
python analyze_sequence.py --sequence "MVKVYAPASSANMSVGFDVL" --id "Test" --basic-only
```

### Full Pipeline Tests (Requires Perl)
```bash
# Test with example data (requires repo/protein-sol/ to be available)
python predict_solubility.py --input ../examples/data/example.fasta --show-results
python batch_predict.py --input ../examples/data/ --workers 1
```

## Known Limitations

1. **Perl Pipeline Dependency**: Most functionality requires the `repo/protein-sol/` Perl scripts
2. **Working Directory**: Perl scripts need specific file setups in working directories
3. **Error Handling**: Perl script errors are captured but not deeply analyzed
4. **Performance**: Single-threaded Perl execution for individual predictions

## Success Criteria Met ✅

- [x] All verified use cases have corresponding scripts
- [x] Each script has a clearly defined main function (`run_<name>()`)
- [x] Dependencies minimized - only pandas and standard library
- [x] Repo-specific code isolated in shared library with lazy loading
- [x] Configuration externalized to `configs/` directory
- [x] Scripts work for basic functionality (sequence analysis basic mode)
- [x] CLI interfaces functional with proper help text
- [x] MCP-ready function signatures designed