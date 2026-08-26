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
- [x] Stage 2.1: Entity schemas
- [x] Stage 2.2: Event schemas
- [x] Stage 2.3: Observable / ground-truth separation
- [x] Stage 2.4: Provenance models
- [x] Stage 2.5: Calibration metric models
- [x] Stage 2.6: Registry integration
- [x] Stage 3: Feature / Dataset Registry Population
- [ ] Stage 4+: See implementation plan

## Registry Configuration

The single source of truth for the system's calibration and metadata configuration is the `ProvenanceRegistry`. 

### Datasets
- **PaySim (`paysim_v1`)**: Used for numerical transaction distributions and category mapping. CC BY 4.0.
- **IEEE-CIS Fraud Detection (`ieee_cis_fraud`)**: Used for categorical device distributions. Kaggle Rules.

### Provenance Tiers
Features are strictly categorized to prevent unsupported data claims:
- **`TIER_1_LEARNED`**: Empirically learned directly from raw reference data (e.g., transaction amounts).
- **`TIER_2_DERIVED`**: Computed through explicit derivation rules applied to raw features (e.g., average typical amount).
- **`TIER_3_DOMAIN_MODELED`**: Synthetically generated based on domain assumptions (e.g., long-term beneficiary relationships), as these are missing from public data.

### Calibration Modes
- **`RAW_DATA`**: Computed by our pipeline using locally available reference data.
- **`REFERENCE_STATISTICS`**: Sourced from published papers or reports (requires citation).

### Known Limitations
- The realism of the generated data is bounded by the public datasets used for calibration.
- PaySim does not capture real-world tail behavior or complex multi-currency geography.
- IEEE-CIS device information is hashed/obfuscated, limiting exact categorical recovery.
- Long-term behavioral state (like beneficiary graphs over years) is domain-modeled rather than learned, due to lack of public telemetry spanning long durations.
