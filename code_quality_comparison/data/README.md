# Code Quality Comparison Data Templates

This directory contains template CSV files showing the expected format for manual data entry.

## File Structure

For each implementation, create a subdirectory with these 4 CSV files:

### 1. `code_quality_summary.csv`

Contains summary statistics for each linting tool.

**Required columns:**

- `Tool`: Name of the linting tool (bandit, ruff, mypy, etc.)
- `Total Issues (A excl)`: Number of issues found (excluding Radon rank A)
- `Files Analyzed`: Number of files analyzed by the tool
- `Issues per File`: Average issues per file

### 2. `detailed_issues.csv` (Optional)

Contains individual issue details for further analysis.

**Required columns:**

- `tool`: Name of the tool that found the issue
- `file`: File path where issue was found
- `line`: Line number of the issue
- `severity`: Severity level (error, warning, etc.)
- `message`: Description of the issue

### 3. `radon_complexity.csv`

Contains cyclomatic complexity scores for functions/methods.

**Required columns:**

- `file`: File path
- `function`: Function or method name
- `line`: Line number where function starts
- `complexity`: Cyclomatic complexity score
- `rank`: Radon complexity rank (A, B, C, D, E, F)
- `type`: Type of code block (function, method, class)

### 4. `radon_maintainability.csv`

Contains maintainability index scores for files.

**Required columns:**

- `file`: File path
- `mi_score`: Maintainability index score (0-100)
- `mi_rank`: Radon maintainability rank (A, B, C, D, E, F)

## Directory Structure Example

```
code_quality_comparison/data/
├── claude_code_with_tuning/
│   ├── code_quality_summary.csv
│   ├── detailed_issues.csv
│   ├── radon_complexity.csv
│   └── radon_maintainability.csv
├── claude_code_no_tuning/
│   ├── code_quality_summary.csv
│   ├── detailed_issues.csv
│   ├── radon_complexity.csv
│   └── radon_maintainability.csv
└── ... (other implementations)
```

## Usage

1. Copy the template files to each implementation subdirectory
2. Replace the template data with actual results from your code quality analysis
3. Run the comparison notebook to generate visualizations and analysis
4. The notebook will automatically detect and load all available data files

## Notes

- All CSV files should use comma separators
- File paths should be relative to the project root
- Missing files will be handled gracefully (empty DataFrames)
- The `detailed_issues.csv` file is optional but provides richer analysis capabilities
