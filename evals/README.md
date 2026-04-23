# CampaignPilot Evaluation Framework

A production-quality evaluation framework for CampaignPilot B2B SaaS marketing automation agents. Provides deterministic metrics, LLM-as-judge evaluation, comprehensive reporting, and regression detection.

## Architecture

```
evals/
├── __init__.py                 # Framework exports
├── metrics/
│   ├── __init__.py
│   ├── deterministic.py       # Non-LLM metrics (completeness, budget, SQL, safety)
│   ├── llm_judge.py           # LLM-as-judge metrics (strategy, brand voice, insights)
│   └── brand_safety.py        # Brand safety wrapper
├── runner.py                   # Core evaluation harness & CLI
├── rubrics/
│   ├── strategist_rubric.json  # Metric definitions for strategist agent
│   ├── creative_rubric.json    # Metric definitions for creative agent
│   └── analyst_rubric.json     # Metric definitions for analyst agent
└── dashboard/
    └── app.py                  # Streamlit dashboard for monitoring
```

## Metrics

### Deterministic Metrics

#### CompletenessMetric
Validates that required fields are present and non-empty.
- **Scale**: 0.0-1.0 (fraction of required fields present)
- **Pass Threshold**: 0.8
- **Default Required Fields**: `recommended_channels`, `budget_split`, `primary_message_pillar`, `kpis`, `rationale`

```python
from evals.metrics import CompletenessMetric

metric = CompletenessMetric(
    required_fields=["headline", "body", "cta"]
)
result = metric.evaluate(agent_output, golden_example)
```

#### BudgetRealismMetric
Validates budget allocation constraints.
- **Scale**: 0.0-1.0
- **Pass Threshold**: 0.7
- **Checks**:
  - Sum of allocations between 0.95-1.05 (allows rounding)
  - Each channel 5%-80% of budget
  - At least one channel allocated

```python
from evals.metrics import BudgetRealismMetric

metric = BudgetRealismMetric()
result = metric.evaluate(agent_output, golden_example)
# Check result.details for violations
```

#### SqlAccuracyMetric
Validates SQL query structure and execution.
- **Scale**: 0.0-1.0
- **Pass Threshold**: 0.6
- **Scoring**:
  - 1.0: Valid structure + executes successfully
  - 0.5: Valid structure but execution fails
  - 0.0: Invalid syntax

```python
from evals.metrics import SqlAccuracyMetric

# With optional DB execution
metric = SqlAccuracyMetric(db_query_tool=query_runner)
result = metric.evaluate(agent_output, golden_example)
```

#### SafetyMetric
Checks marketing copy for brand safety violations.
- **Scale**: 1.0 (fully safe) or 0.0 (violations)
- **Pass Threshold**: 1.0 (must be fully safe)
- **Integrates**: SafetyChecker for compliance

```python
from evals.metrics import SafetyMetric
from tools.safety_checker import SafetyChecker

safety_checker = SafetyChecker()
metric = SafetyMetric(safety_checker=safety_checker)
result = metric.evaluate(agent_output, golden_example)
```

### LLM-as-Judge Metrics

All LLM judges use Claude Haiku for cost efficiency. Scores are on 1-5 scale.

#### StrategicCoherenceMetric
Evaluates logical consistency of B2B campaign strategy.
- **Scale**: 1-5
- **Pass Threshold**: 3.0
- **Judging Dimensions**:
  - Channel selection appropriateness
  - KPI relevance and specificity
  - Budget justification
  - Rationale strength

```python
from evals.metrics import StrategicCoherenceMetric

metric = StrategicCoherenceMetric(model="claude-haiku-4-5-20251001")
result = metric.evaluate(agent_output, golden_example)
```

#### BrandVoiceMetric
Evaluates marketing copy against Lumen Analytics brand voice.
- **Scale**: 1-5
- **Pass Threshold**: 3.0
- **Brand Attributes**: Professional, data-forward, anti-hype, outcomes-obsessed, second person
- **Prohibited Phrases**: game-changing, revolutionary, disruptive, leverage, synergize, etc.

```python
from evals.metrics import BrandVoiceMetric

metric = BrandVoiceMetric()
result = metric.evaluate(agent_output, golden_example)
# result.details["reasoning"] explains the score
```

#### InsightQualityMetric
Evaluates depth and actionability of marketing analytics insights.
- **Scale**: 1-5
- **Pass Threshold**: 3.0
- **Evaluation Dimensions**:
  - Finding clarity (vs. raw number restatement)
  - Root cause analysis
  - Quantified implications
  - Actionable recommendations
  - Risk/tradeoff consideration

```python
from evals.metrics import InsightQualityMetric

metric = InsightQualityMetric()
result = metric.evaluate(agent_output, golden_example)
```

### BrandSafetyMetric
Wrapper around SafetyChecker for brand compliance.
- **Scale**: 0.0-1.0
- **Scoring**:
  - 1.0: No violations
  - 0.5: Low severity violations
  - 0.0: Medium/high severity violations

## EvalRunner

Main evaluation harness.

### Basic Usage

```python
from evals.runner import EvalRunner
from evals.metrics import (
    CompletenessMetric,
    StrategicCoherenceMetric,
    BudgetRealismMetric
)

# Load golden dataset
dataset = EvalRunner.load_golden_dataset("golden_dataset.json")

# Define metrics
metrics = [
    CompletenessMetric(),
    StrategicCoherenceMetric(),
    BudgetRealismMetric(),
]

# Run evaluation
runner = EvalRunner()
report = runner.run(
    agent=my_agent,
    golden_dataset=dataset,
    metrics=metrics,
    agent_name="strategist",
    dataset_version="v1"
)

# Print beautiful report
runner.print_report(report)
```

### EvalReport Structure

```python
@dataclass
class EvalReport:
    agent_name: str                          # "strategist", "creative", etc.
    dataset_version: str                     # "v1"
    total_examples: int                      # 20
    example_results: list[ExampleResult]     # Per-example results
    aggregate_scores: dict[str, dict]        # Metric -> {mean, min, max, p25, p75, pass_rate}
    regression_flags: list[dict]             # Metrics that dropped >5% vs baseline
    total_input_tokens: int                  # For cost tracking
    total_output_tokens: int
    estimated_cost_usd: float
    run_duration_ms: float
    passed: bool                             # Overall pass/fail
```

### Saving Results to Database

EvalRunner automatically saves to PostgreSQL when DATABASE_URL is set:

```bash
export DATABASE_URL=postgresql://user:password@host/dbname

python -m evals.runner --agent strategist --dataset golden_dataset.json
```

Expected schema:
```sql
CREATE TABLE eval_runs (
    id SERIAL PRIMARY KEY,
    agent_name TEXT,
    dataset_version TEXT,
    total_examples INT,
    passed BOOLEAN,
    aggregate_scores JSONB,
    input_tokens INT,
    output_tokens INT,
    estimated_cost_usd FLOAT,
    duration_ms FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE eval_examples (
    id SERIAL PRIMARY KEY,
    eval_run_id INT REFERENCES eval_runs(id),
    example_id TEXT,
    metric_scores JSONB,
    metric_passed JSONB,
    errors JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## CLI

```bash
# Run strategist evaluation
python -m evals.runner --agent strategist --dataset golden_dataset.json

# Skip expensive LLM-as-judge metrics
python -m evals.runner --agent analyst --dataset data.json --no-llm-judge

# Don't save to DB
python -m evals.runner --agent creative --dataset data.json --no-save

# Custom dataset version
python -m evals.runner --agent optimizer --dataset data.json --dataset-version v2.1
```

## Dashboard

Real-time performance monitoring with Streamlit.

```bash
streamlit run evals/dashboard/app.py
```

Features:
- Latest scores by agent and metric
- Score trends over time
- Cost tracking by agent
- Regression detection (>5% drop)
- Run history table
- Summary statistics

Requires PostgreSQL connection via DATABASE_URL.

## Golden Dataset Format

JSON file with examples:

```json
[
  {
    "id": "example_001",
    "input": {
      "goal": "Drive DBAs to our Lumen Analytics trial",
      "segment": "Fortune 500 IT Directors",
      "budget_usd": 50000,
      "campaign_duration_days": 30
    },
    "expected_output": {
      "recommended_channels": ["LinkedIn", "Email", "Events"],
      "budget_split": {"LinkedIn": 0.45, "Email": 0.35, "Events": 0.20},
      "primary_message_pillar": "ROI impact through data transparency",
      "kpis": ["Conversion rate", "CAC", "Pipeline influence"],
      "rationale": "Target high-intent professionals where Lumen has strong positioning..."
    }
  }
]
```

## Installation

```bash
pip install -r evals/requirements.txt
```

## Configuration

Set environment variables:

```bash
# Claude API key (required for LLM judges)
export ANTHROPIC_API_KEY=sk-ant-...

# PostgreSQL connection (optional, for saving results)
export DATABASE_URL=postgresql://user:password@host/dbname
```

## Cost Estimation

Claude Haiku pricing (as of 2024):
- Input: $0.80 per 1M tokens
- Output: $4.00 per 1M tokens

Example costs:
- 10 examples with 3 LLM judges: ~$0.02-0.05 per run
- 100 examples: ~$0.20-0.50 per run

## Rubrics

Agent-specific metric configurations in `evals/rubrics/`:

### strategist_rubric.json
- strategic_coherence (40% weight)
- completeness (30%)
- budget_realism (30%)

### creative_rubric.json
- brand_voice (40%)
- brand_safety (30%)
- completeness (30%)

### analyst_rubric.json
- insight_quality (40%)
- sql_accuracy (35%)
- completeness (25%)

## Extending the Framework

### Create a Custom Metric

```python
from evals.metrics.deterministic import BaseMetric, MetricResult

class CustomMetric(BaseMetric):
    name = "custom_metric"
    pass_threshold = 0.7
    
    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        # Your evaluation logic here
        score = calculate_score(agent_output, golden_example)
        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=score >= self.pass_threshold,
            details={"custom_data": "..."}
        )
```

### Integration with CI/CD

```bash
# In CI pipeline
python -m evals.runner --agent strategist --dataset golden_dataset.json
# Exit code 0 if passed, 1 if failed
```

## Best Practices

1. **Golden Dataset Quality**: Ensure examples are representative, diverse, and have correct expected outputs
2. **Metric Weights**: Adjust pass thresholds in rubrics based on business priorities
3. **Regression Monitoring**: Check regressions dashboard weekly; set alerts for >5% drops
4. **Cost Tracking**: LLM judges are cheap; batch evaluations to minimize API calls
5. **Error Handling**: All metrics catch exceptions; check `ExampleResult.errors` for failures

## Troubleshooting

**LLM Judge returning 0.0 scores**: Check ANTHROPIC_API_KEY is set and valid

**SQL Accuracy always failing**: Verify db_query_tool is passed and working

**Dashboard shows "Using mock data"**: Ensure DATABASE_URL is set correctly

**Regression detection not working**: Database must have previous eval_runs records

## License

Internal use only.
