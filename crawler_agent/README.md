# Crawler Agent

This project uses AI agents to extract structured data from crowdfunding project pages.

## Setup

Set the required environment variable, for example in a `.env` file:

```bash
GEMINI_API_KEY="YOUR_API_KEY"
```

## Workflow

The project supports two main evaluation workflows: a manual validation process and an automated one using an LLM as a judge.

### Manual Validation Workflow

#### 1. Run Agents

Process all HTML files in `single_samples/` to generate structured JSON output for each of the three agents (`Basic`, `Function`, and `Expert`).

```bash
python compare_agents.py
```

This will populate the `results/basic`, `results/function`, and `results/expert` directories.

#### 2. Validate Results (Manual)

Run the interactive validation script. This will ask you to manually confirm the correctness of the data extracted by each agent for each project.

```bash
python validate_results.py
```

Validation files are saved in `results/validation/`.

#### 3. Calculate Scores (Manual)

After manually validating the results, run the scoring script to generate a final report on agent performance based on your validation.

```bash
python calculate_scores.py
```

This creates `results/scoring_report.json` with a detailed accuracy breakdown.

---

### LLM Judge Workflow

This workflow uses a Gemma model to automatically evaluate the agents' performance.

#### 1. Run Agents

This step is the same as the manual workflow.

```bash
python compare_agents.py
```

#### 2. Run LLM Judge

Run the automated validation script. This uses a Gemma model to evaluate the correctness of the data extracted by each agent.

```bash
python llm_judge.py
```

LLM validation files are saved in `results/llm_validation/`.

#### 3. Calculate Scores (LLM)

After the LLM judge has evaluated the results, run the scoring script with the `--llm` flag to generate a report based on the LLM's judgments.

```bash
python calculate_scores_llm.py
```

This creates `results/scoring_report_llm.json`.

#### 4. Calculate Confusion Matrix

After generating both manual and LLM scoring reports, you can run this script to compare the LLM judge's decisions against the human-provided ground truth.

```bash
python calculate_confusion_matrix.py
```

This creates `results/llm_judge_confusion_matrix_report.json`, which provides metrics on the LLM judge's accuracy.

---

## Programmatic Usage

You can also import and use the agents directly in your own Python scripts without using the interactive runners.

```python
import os
from dotenv import load_dotenv
from crawler_agent.agents.expert import ExpertAgent

# Load API key from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize the agent
agent = ExpertAgent(api_key=api_key)

# Define file paths
html_file = "single_samples/some_project.html"
config_file = "configs/single_project_config.json"
output_file = "output.json"

# Process the file and save the result
agent.process_and_save(html_file, config_file, output_file)

print(f"Extraction complete. Results saved to {output_file}")
```
