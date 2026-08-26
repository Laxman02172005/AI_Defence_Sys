# Red Team AI — Module 1

Synthetic payment-fraud attack trace generation for payment-security research.

## Purpose

Build a calibrated synthetic payment world, inject research-grounded attack behavior,
use AI to compose and vary scenarios, simulate observable consequences, and
quantitatively validate realism and novelty before using the traces to test a
fraud detector.

This is a **controlled simulation environment**. It generates only synthetic entities,
events, relationships, and attack scenarios. It never interacts with real payment
systems or generates real payment requests.

## Architecture

```
Reference Data → Statistical Realism
Normal World → Legitimate Behavioral Context
Attack Signature Library → Research-grounded Attack Plausibility
LLM → Structured Scenario Composition
Simulation Engine → Actual Event Generation
Validator → Measurable Realism/Novelty Verification
```

## Setup

```bash
pip install -r requirements.txt
pip install -e ".[dev]"
```

## Tests

```bash
pytest tests/ -v
```

## Project Status

- [x] Stage 1: Repository & environment inspection
- [ ] Stage 2.1: Entity schemas
- [ ] Stage 2.2: Event schemas
- [ ] Stage 2.3: Observable / ground-truth separation
- [ ] Stage 2.4: Provenance models
- [ ] Stage 2.5: Calibration metric models
- [ ] Stage 2.6: Registry integration
- [ ] Stage 3+: See implementation plan
