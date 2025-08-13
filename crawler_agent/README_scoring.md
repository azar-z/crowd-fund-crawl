# Agent Scoring System

This directory contains an independent scoring system for comparing the accuracy of Simple and Advanced crawler agents.

## Overview

The scoring system consists of two independent scripts:

1. **`validate_results.py`** - Interactive validation per project
2. **`calculate_scores.py`** - Score calculation across all projects

## How to Use

### Step 1: Validate Individual Projects

Run the validation script for each project you want to score:

```bash
# Validate a specific project
python validate_results.py hamafarin
python validate_results.py dongi
python validate_results.py karencrowd
```

This will:
- Load extraction results for both agents
- Ask you to validate each field interactively
- Save validation results to `results/validation/{project}_validation.json`

### Step 2: Calculate Overall Scores

After validating one or more projects, calculate the overall scores:

```bash
python calculate_scores.py
```

This will:
- Load all validation files
- Calculate accuracy scores (0-100) for both agents
- Generate a detailed performance report
- Save results to `results/scoring_report.json`

## Validation Process

For each field in each project, you'll be asked:

```
📋 Field: company
🤖 Simple Agent: شرکت غذای سالم پارس
✅ Is this correct? (y/n/s=skip):
```

**Options:**
- `y/yes/1` = Correct extraction
- `n/no/0` = Incorrect extraction  
- `s/skip` = Skip this field (won't count toward score)

## Scoring Logic

- **Final Score (0-100)**: `(Correct Fields / Total Evaluated Fields) × 100`
- **Skipped fields** are excluded from scoring
- **Missing data** for an agent doesn't affect the other agent's score
- **Field-specific accuracy** is tracked separately

## Output Files

### Validation Files (`results/validation/`)
```json
{
  "project_name": "hamafarin",
  "validation_timestamp": "2024-01-15T10:30:00",
  "simple_agent": {
    "available": true,
    "field_validations": {
      "company": {
        "value": "شرکت غذای سالم پارس",
        "is_correct": true
      }
    }
  },
  "advanced_agent": { ... }
}
```

### Scoring Report (`results/scoring_report.json`)
```json
{
  "report_timestamp": "2024-01-15T10:35:00",
  "final_scores": {
    "simple_agent": 85.5,
    "advanced_agent": 92.3
  },
  "agent_statistics": { ... },
  "project_details": [ ... ]
}
```

## Example Workflow

```bash
# 1. Generate some results first
python compare_agents.py  # with project_name = "hamafarin"

# 2. Validate the results
python validate_results.py hamafarin

# 3. Repeat for other projects
python validate_results.py dongi
python validate_results.py karencrowd

# 4. Calculate final scores
python calculate_scores.py
```

## Features

- ✅ **Independent of comparison process** - Works with any extraction results
- ✅ **Interactive validation** - Manual verification of each field
- ✅ **Supports missing data** - Handles cases where one agent failed
- ✅ **Field-specific tracking** - See which fields each agent handles better
- ✅ **Project-by-project breakdown** - Detailed per-project analysis
- ✅ **Skippable fields** - Don't count uncertain validations
- ✅ **JSON output** - Machine-readable results for further analysis
