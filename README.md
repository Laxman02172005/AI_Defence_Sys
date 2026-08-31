# Blue Team Integration Specification
## AI Defense Lab — Red Team / Blue Team Payment Security

**Document purpose:** Technical handoff and integration contract for the Blue Team.

---

## 1. Purpose and Scope

This document defines how the Blue Team should consume the Red Team's synthetic payment-fraud attack corpora.

The Red Team provides realistic, stateful, synthetic attack traces for two attack families:

- `ACCOUNT_TAKEOVER` (ATO)
- `AUTHORIZED_PUSH_PAYMENT` (APP)

The Blue Team must use the observable telemetry as model input and use ground truth only for labeling, stratification, validation, and evaluation.

**Core rule:**

> `observable_trace` is model input. `ground_truth` is evaluation metadata and must never be used as a predictive feature.

The environment is entirely synthetic and does not interact with real payment systems, banking infrastructure, or real customer accounts.

---

## 2. Red Team → Blue Team Integration Contract

Each persisted corpus record has two major components:

```text
AttackRecord
├── observable_trace
└── ground_truth
```

### 2.1 Observable Trace

This represents what a real payment-security system would observe.

It contains events such as:

- session login
- device registration
- authentication activity
- beneficiary activity
- transactions
- transaction failures
- successful transactions
- channel changes
- behavioral timing
- account-access behavior
- account-modification behavior

Use this component for:

- feature engineering
- model training
- model inference
- behavioral analysis
- sequence modeling
- graph construction

### 2.2 Ground Truth

This represents hidden information about the simulated attack.

It is used for:

- labels
- stratification
- evaluation
- error analysis
- attack-family comparison
- difficulty-specific evaluation

Do **not** pass ground-truth fields into feature extraction or inference.

---

# 3. Delivered Red Team Corpus

The finalized persisted corpora are:

```text
reports/ato_corpus_raw.json
reports/app_corpus_raw.json
```

### Actual delivered counts

| Corpus | Attack family | Persisted traces |
|---|---|---:|
| ATO | `ACCOUNT_TAKEOVER` | 97 |
| APP | `AUTHORIZED_PUSH_PAYMENT` | 156 |
| **Total** | | **253** |

These are the actual persisted counts. They are not the original requested target counts.

### Difficulty distribution

#### ATO

```text
easy       22
medium     25
hard       25
advanced   25
TOTAL      97
```

#### APP

```text
easy        6
medium     50
hard       50
advanced   50
TOTAL     156
```

The lower EASY counts are a known consequence of the generator's structural diversity/entropy constraints and attempt budgets. Do not interpret the lower count as missing corruption or as a failed schema.

---

# 4. Corpus Record Loading

Python:

```python
import json

with open("reports/ato_corpus_raw.json", "r") as f:
    ato = json.load(f)

with open("reports/app_corpus_raw.json", "r") as f:
    app = json.load(f)

records = ato + app

print("Total records:", len(records))
```

Each record can then be separated:

```python
for record in records:
    observable = record["observable_trace"]
    ground_truth = record["ground_truth"]
```

---

# 5. Observable Data Rules

The observable trace should be treated as the authoritative input boundary for Blue Team modeling.

Typical observable information includes:

```text
event_id
timestamp
event_type
customer_id
session_id
device_id
beneficiary information where present
transaction identifiers
transaction amount
transaction status
channel information where present
```

The exact schema in the persisted JSON should be treated as authoritative. Do not infer fields that are not actually present.

### Important

Account balances such as:

```text
pre_balance
post_balance
```

are intentionally not exposed in the flattened observable transaction representation.

The simulator nevertheless maintains balance consistency internally during generation.

Therefore:

- Blue Team **must not depend on `pre_balance` or `post_balance`**
- balance-derived model features must instead be reconstructed from observable history where possible
- generation-time ledger correctness is an internal Red Team invariant

---

# 6. Ground Truth Fields

Ground truth can contain information such as:

```text
attack_id
attack_family
attack_difficulty
hidden_objective
phase records
planner metadata
linked event IDs
```

Depending on the exact schema/version, additional ground-truth metadata may exist.

### Ground-truth usage policy

Allowed:

```text
Ground truth
     ↓
Labels
     ↓
Evaluation
```

Not allowed:

```text
Ground truth
     ↓
Feature engineering
     ↓
Model
```

For example, this is forbidden:

```python
features["attack_family"] = ground_truth["attack_family"]
```

This would constitute label leakage.

---

# 7. Attack Family: ATO

## `ACCOUNT_TAKEOVER`

ATO represents unauthorized access to a customer's account by another party.

Typical behavioral characteristics include:

- new-device registration
- session/login activity
- transaction activity following account access
- transaction fragmentation
- failed transaction attempts followed by lower successful amounts
- timing variation
- increasingly sophisticated low-and-slow behavior at higher difficulty

### Observable indicators

Potential features include:

- new-device indicators
- login frequency
- device changes
- transaction frequency
- transaction fragmentation
- failed-to-successful transaction transitions
- amount progression
- transaction timing
- transactions per session
- transactions per time window

These are behavioral indicators, not ground-truth labels.

---

# 8. Attack Family: APP

## `AUTHORIZED_PUSH_PAYMENT`

APP represents a legitimate customer being socially engineered into authorizing payments.

Typical behavioral characteristics include:

- use of an existing/trusted device
- existing session activity
- delayed payment execution
- hesitation gaps
- beneficiary/payment behavior
- failed attempts caused by transaction limits
- lower subsequent successful amounts
- difficulty-dependent behavioral variation

### Observable indicators

Potential features include:

- trusted-device usage
- session continuity
- beneficiary-before-transaction sequence
- time between relevant events
- failed transaction retries
- amount reduction after failures
- transaction timing
- session-to-payment relationships

---

# 9. Difficulty Semantics

The generator uses four difficulty levels:

```text
easy
medium
hard
advanced
```

Difficulty describes how difficult the simulated attack is intended to be for detection.

It is **not** an observable feature.

### ATO

Higher difficulty generally introduces more subtle behavioral variation, including low-and-slow activity and more complex timing/transaction patterns.

### APP

Higher difficulty can introduce longer hesitation periods, friction, and multiple failed/retried payment attempts.

### Important

The Blue Team should evaluate performance separately by difficulty.

Do not train a model using `attack_difficulty` as an input feature.

---

# 10. Recommended Feature Engineering

Features should be constructed from observable telemetry.

## Transaction features

Examples:

```text
transaction count
total transaction amount
mean transaction amount
median transaction amount
maximum transaction amount
amount variance
failed transaction count
successful transaction count
failure-to-success ratio
```

## Temporal features

```text
transactions per hour
events per hour
time between login and transaction
time between beneficiary activity and transaction
time between failed and successful attempts
session duration
inter-event intervals
```

## Session features

```text
transactions per session
login count
authentication failures
session reuse
new session frequency
```

## Device features

```text
new-device indicator
device count per customer
device changes
device-to-customer relationships
```

## Beneficiary features

```text
beneficiary additions
beneficiary-before-payment sequence
beneficiary reuse
customer-beneficiary frequency
time from beneficiary addition to payment
```

## Sequence features

```text
event-type sequences
transition frequencies
failed → successful transitions
login → transaction transitions
device → session → transaction transitions
```

## Graph features

Potential graph entities:

```text
Customer
 ├── Device
 ├── Session
 ├── Beneficiary
 └── Transaction
```

Potential relationship features include:

- degree
- shared devices
- shared beneficiaries
- transaction relationships
- session relationships
- temporal relationships

---

# 11. Features That Must NOT Be Used

Never use these as predictive model inputs:

```text
attack_family
attack_difficulty
hidden_objective
planner_metadata
internal phase labels
ground-truth attack objective
ground-truth-only metadata
internal simulator state
pre_balance
post_balance
```

### Attack IDs

`attack_id` is an identifier, not a behavioral feature.

Do not allow the model to learn from ID formatting, prefixes, ordering, or generated values.

---

# 12. Train/Test Split Rules

Split at the **attack-record/trace level**.

Do not split individual events from the same attack trace across training and test sets.

Bad:

```text
Trace A events 1-5 → training
Trace A events 6-10 → test
```

Good:

```text
Trace A → training
Trace B → training
Trace C → test
Trace D → test
```

Where graph/entity leakage is relevant, additionally consider grouping by customer/entity relationships.

Keep ground truth completely separate from the feature pipeline.

---

# 13. Recommended Blue Team Pipeline

```text
                 Red Team Corpus
                       │
                       ▼
                Schema Validation
                       │
                       ▼
              Observable Extraction
                       │
                       ▼
                Event Normalization
                       │
                       ▼
                Feature Engineering
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
       XGBoost       Graph        Autoencoder
          │          Detector          │
          └────────────┼───────────────┘
                       ▼
                  Risk Fusion
                       │
                       ▼
                Decision Policy
                       │
                       ▼
             Allow / Verify / Review /
                    Block
                       │
                       ▼
                Explainability
                       │
                       ▼
                Miss Collection
                       │
                       ▼
               Hard Examples
                       │
                       ▼
                Re-evaluation
```

---

# 14. Existing Blue Team Components

The project architecture contains:

### Stage 1 — Rule Filter

Fast deterministic behavioral checks.

### Stage 2 — XGBoost

Tabular behavioral detection using engineered event-sequence features.

Representative features include:

- transaction counts
- session-login counts
- device registrations
- beneficiary additions
- total events
- transactions per hour
- transactions per session
- authentication failures
- new-device indicators
- failed transactions
- amount statistics
- amount trends
- channel diversity
- event timing

Verified model artifact:

```text
blue_team_output_FROZEN/xgb_model.joblib
```

### Stage 3 — Graph Detector

Models relationships among:

```text
Customer
Device
Session
Beneficiary
Transaction
```

Verified result:

```text
blue_team_output_FROZEN/gnn_results.json
```

### Stage 4 — Autoencoder

Provides an independent anomaly signal through reconstruction error.

Verified result:

```text
blue_team_output_FROZEN/stage4_autoencoder_results.json
```

### Stage 5 — Risk Fusion

Combines:

```text
Rule signal
XGBoost signal
Graph signal
Autoencoder signal
```

into a unified risk score.

Artifact:

```text
blue_team_output_FROZEN/risk_fusion_results.json
```

### Stage 6 — Decision Policy

Maps risk to operational action:

```text
LOW       → Allow
MEDIUM    → Verification / Review
HIGH      → Block / Escalate
```

Artifacts:

```text
frozen_reports/decision_policy_results.json
frozen_reports/decision_policy_sensitivity_results.json
```

### Stage 7 — Explainability

Global:

```text
blue_team_output_FROZEN/explainability/global_feature_importance.json
blue_team_output_FROZEN/explainability/global_shap_summary.png
```

Case-level:

```text
blue_team_output_FROZEN/explainability/case_reports.json
blue_team_output_FROZEN/explainability/case_reports.md
```

---

# 15. Normal / Legitimate Data

The Red Team corpus is an attack corpus.

It should not automatically be treated as the complete legitimate-vs-fraud training dataset.

The intended combination is:

```text
Normal World / legitimate activity
            +
        ATO attacks
            +
        APP attacks
            ↓
     Blue Team dataset
```

The Red Team attacks provide controlled positive/adversarial cases.

---

# 16. Evaluation Protocol

At minimum evaluate:

```text
Precision
Recall
F1
ROC-AUC
PR-AUC
Confusion Matrix
```

Evaluate separately for:

```text
All attacks
ATO
APP
ATO by difficulty
APP by difficulty
```

Also examine:

```text
false positives
false negatives
missed ATO
missed APP
performance by difficulty
```

Do not rely only on aggregate accuracy.

---

# 17. Data Quality Verification

The final persisted corpora were verified with the following results:

| Check | Result |
|---|---:|
| ATO records | 97 |
| APP records | 156 |
| Malformed ATO records | 0 |
| Malformed APP records | 0 |
| ATO duplicate attack IDs | 0 |
| APP duplicate attack IDs | 0 |
| Cross-family attack-ID intersection | 0 |
| Ground-truth/observable pairing mismatches | 0 |
| Observable leakage | 0 |
| Observable events scanned | 1,783 |
| Chronology failures | 0 |
| ATO schema failures | 0 |
| APP schema failures | 0 |

The full Red Team test suite at the final verification point:

```text
468 passed
0 failed
0 warnings
```

with the command:

```powershell
$env:PYTHONPATH="src"
pytest tests/ -v -W error::DeprecationWarning
```

---

# 18. Ground-Truth / Observable Isolation

The critical security property is separation between:

```text
WHAT THE ATTACKER ACTUALLY DID
              vs.
WHAT THE BANK WOULD OBSERVE
```

Observable traces were scanned for ground-truth fields.

Final result:

```text
1,783 observable events scanned
0 leakage findings
```

The observable corpus must remain the only input to the Blue Team feature pipeline.

---

# 19. Corpus Pairing

Every persisted record contains its observable trace and corresponding ground truth.

The verification found:

```text
Pairing mismatches: 0
```

Ground-truth `linked_event_ids` were checked against the event IDs in the corresponding observable trace.

Therefore the ground truth can be used after inference to determine whether detected events correspond to the actual simulated attack events.

---

# 20. Chronology

All observable event arrays were verified to be ordered chronologically.

Result:

```text
253 traces checked
0 chronology failures
```

Blue Team should preserve timestamps as temporal information rather than arbitrarily shuffling events inside an individual trace.

---

# 21. Novelty and Diversity

The Red Team novelty engine tracks fingerprints by:

```text
attack family
+
difficulty bucket
```

Final corpus audit:

```text
ATO duplicate fingerprints: 6
APP duplicate fingerprints: 3
```

These duplicates occurred across different difficulty buckets.

There were zero duplicate fingerprints within the same difficulty bucket.

This means the duplicates do not indicate a failure of the within-bucket novelty gate.

Do not use the fingerprint as a model feature.

---

# 22. PRNG and Reproducibility

A cross-family PRNG collision was identified and fixed.

The issue was caused by the simulator deriving its random stream from the raw seed without incorporating attack family.

The implemented solution salts the seed using the attack family before constructing the internal `random.Random` stream.

Conceptually:

```text
raw seed
   +
attack family
   ↓
stable salted seed
   ↓
random.Random(...)
```

This prevents two different attack families from receiving the same random stream when the same raw seed is reused.

A dedicated regression test verifies the original collision condition.

---

# 23. Important ATO Acceptance-Rate Clarification

An earlier ATO acceptance figure of:

```text
100 / 131 = 76.33%
```

must **not** be used as the modern ATO benchmark.

That number came from an earlier Stage 15 measurement before the defensive novelty filtering used in the later pipeline.

The apples-to-apples Stage 23 baseline was:

```text
99 / 676 = 14.64%
```

The isolated regression tests after the PRNG fix produced:

```text
Pre-fix:  98 / 643 = 15.24%
Post-fix: 97 / 627 = 15.47%
```

These are consistent with the modern approximately 15% ATO acceptance regime.

Therefore the PRNG fix was not shown to degrade ATO generation quality.

---

# 24. Known Limitations

### Synthetic data

Generated traces are synthetic and their realism is bounded by the reference data and domain modeling.

### Public-data coverage

Public datasets do not contain every type of payment-security telemetry required for long-term behavioral modeling.

### Domain-modeled behavior

Some long-term behavioral relationships are explicitly modeled rather than directly learned from public data.

Examples include:

- long-term beneficiary relationships
- extended behavioral state
- certain relationship-level signals

### APP EASY diversity

The EASY APP bucket has limited structural diversity. The generator does not manufacture artificial diversity merely to increase record counts.

### ATO EASY budget

The ATO EASY bucket can hit its attempt budget because of structural novelty/entropy limits.

### Hard-example diversity

The current hard-example investigations found that some generated hard examples can be highly similar in model-feature space.

### Evaluation stability

Round-to-round ML metrics can change due to:

- sample-count changes
- cross-validation partitioning
- fold reassignment
- newly introduced hard examples

Future comparisons should use fixed evaluation sets and controlled folds.

---

# 25. Security Boundary

This project is a controlled payment-security research simulation.

It:

- does not access real banking systems
- does not interact with payment networks
- does not submit real payment requests
- does not target real accounts
- does not contain real customer payment information
- uses synthetic entities and simulated events

The Red Team is intended for controlled defensive evaluation.

---

# 26. Repository Map

Important Red Team locations:

```text
src/red_team/
├── attacks/
├── schemas/
├── validation/
├── world/
└── ml/
```

Persisted attack corpora:

```text
reports/
├── ato_corpus_raw.json
└── app_corpus_raw.json
```

Important handoff document:

```text
RED_TEAM_HANDOFF.md
```

Blue Team artifacts:

```text
blue_team_output_FROZEN/
frozen_reports/
```

Web prototype:

```text
web_prototype/
streamlit_app/
```

Tests:

```text
tests/
```

---

# 27. Integration Checklist

Before declaring integration complete:

```text
[ ] Clone repository
[ ] Install requirements
[ ] Configure PYTHONPATH
[ ] Load ATO corpus
[ ] Load APP corpus
[ ] Validate every record against schema
[ ] Separate observable_trace from ground_truth
[ ] Confirm ground_truth is excluded from features
[ ] Inspect event timestamps
[ ] Preserve event ordering
[ ] Add Normal World / legitimate data
[ ] Build trace-level train/test split
[ ] Prevent entity leakage where applicable
[ ] Build transaction features
[ ] Build session features
[ ] Build device features
[ ] Build beneficiary features
[ ] Build temporal features
[ ] Build sequence features
[ ] Build graph features if applicable
[ ] Train/evaluate detector
[ ] Evaluate ATO separately
[ ] Evaluate APP separately
[ ] Evaluate by difficulty
[ ] Calculate precision/recall/F1
[ ] Calculate PR-AUC/ROC-AUC where appropriate
[ ] Analyze false positives
[ ] Analyze false negatives
[ ] Integrate risk fusion
[ ] Integrate decision policy
[ ] Integrate explainability
[ ] Preserve ground-truth-only evaluation path
```

---

# 28. Troubleshooting

### "Why are there only 97 ATO traces?"

97 is the actual persisted qualified corpus. The EASY bucket reached its attempt budget before the requested overall target of 100 was reached.

### "Why are there only 156 APP traces?"

156 is the actual persisted qualified corpus. The EASY bucket has structurally constrained diversity.

### "Can I use `attack_family` as a feature?"

**No.** It is the target label.

### "Can I use `attack_difficulty` as a feature?"

**No.** It is ground-truth metadata.

### "Can I use attack IDs?"

Use them only for record identity/joining. Never as predictive features.

### "Can I use balances?"

Not from the observable attack records. `pre_balance` and `post_balance` are intentionally absent from the flattened observable schema.

### "Can I use ground truth during evaluation?"

Yes. That is its intended purpose.

### "Can I use ground truth during training?"

Only as the target/label or for stratification. Never as an input feature.

---

# 29. Final Red Team → Blue Team Contract

The boundary is:

```text
                 RED TEAM
                    │
                    │
                    ▼
        ┌────────────────────────┐
        │ Observable Attack Data │
        └────────────┬───────────┘
                     │
                     ▼
                 BLUE TEAM
                     │
             feature engineering
                     │
                     ▼
                  models
                     │
                     ▼
                  scores
                     │
                     ▼
                 decisions
```

Ground truth remains on a separate evaluation path:

```text
Ground Truth
     │
     ├── labels
     ├── stratification
     ├── evaluation
     └── error analysis
```

### Non-negotiable rule

> **Blue Team must never use hidden Red Team ground-truth information as an observable behavioral feature.**

The purpose of the Red Team corpus is to provide realistic adversarial behavioral telemetry while preserving a trustworthy distinction between the attacker's hidden intent and the evidence available to a fraud-detection system.

---

## 30. Handoff Summary

### Delivered

```text
ATO corpus:              97 traces
APP corpus:             156 traces
Total attack traces:    253
Observable events:    1,783
```

### Verified

```text
Malformed records:        0
ID collisions:            0
Cross-family ID overlap:  0
GT/observable mismatches: 0
Observable leakage:       0
Chronology failures:      0
Schema failures:          0
Final test failures:      0
```

### Primary files

```text
reports/ato_corpus_raw.json
reports/app_corpus_raw.json
RED_TEAM_HANDOFF.md
BLUE_TEAM_INTEGRATION_SPEC.md
```

### Status

The Red Team corpus and integration boundary are frozen at the documented artifact state. Any regeneration or modification should produce a new versioned evaluation artifact rather than silently replacing the existing baseline.
