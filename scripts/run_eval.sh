#!/usr/bin/env bash

# Wrapper script to run evaluations with runner.py
# Example usage: ./scripts/run_eval.sh --agent strategist --dataset data/golden_datasets/strategist_golden.json

set -e

# Run tests
echo "Running evaluation for CampaignPilot..."

python evals/runner.py "$@"

echo "Evaluation complete."
