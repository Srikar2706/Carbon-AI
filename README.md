# Agentic AI Carbon Ranker MVP

An intelligent agent that normalizes messy AI vendor operational data and ranks them by carbon efficiency.

## Problem
Procurement teams can't compare AI vendors' carbon efficiency from messy, inconsistent logs.

## Solution
An agentic system that:
1. Detects and normalizes messy operational data
2. Computes standardized kWh & tCO₂e metrics
3. Ranks vendors by carbon efficiency
4. Provides procurement-ready insights

## Key Features
- **Agentic Processing**: Planner → Executor → Critic loop with autonomous retry
- **Data Normalization**: Handles mixed units, missing values, fuzzy tokens
- **Carbon Metrics**: tCO₂e, intensity ratios, efficiency scores
- **Green Score**: Composite ranking (0-100) for vendor comparison
- **Dashboard**: Interactive leaderboard and company detail views

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## Demo Flow
1. Show messy input data from multiple vendors
2. Run agent processing with detection → fixes → recompute
3. View leaderboard with rankings and data quality badges
4. Edit raw data and re-run to see rank changes
5. Make procurement decision based on efficiency metrics
