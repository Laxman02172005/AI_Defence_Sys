# AI Defense Lab — Red Team / Blue Team Payment Security

An end-to-end adversarial AI system for payment-security research that **identifies emerging fraud patterns, generates realistic synthetic attacks, detects them using a multi-stage defense pipeline, and feeds detection failures back into adaptive evaluation**.

This project was developed for the **Mastercard Innovation Challenge @ GFF 2026 — AI Defense Lab for Payment Security**.

---

## Overview

Generative AI is making sophisticated payment fraud faster, cheaper, and harder to detect.

Traditional static rules struggle with attacks that continuously change their behavior. This project addresses this problem through a closed-loop:

**Red Team → Blue Team → Adaptive Defense**

The system:

1. **Identifies** emerging and plausible GenAI-enabled payment-fraud attack patterns.
2. **Generates** controlled synthetic attack traces at scale.
3. **Defends** against those attacks using multiple complementary ML detectors.
4. **Fuses** detector outputs into a unified risk score.
5. **Applies** a decision policy to determine the appropriate response.
6. **Explains** individual and global model decisions.
7. **Collects detection misses** as hard examples for future evaluation.
8. **Feeds failures back** into the evaluation loop.

The entire environment operates on **synthetic data** and does not interact with real payment systems or generate real payment requests.

---

# System Architecture

```text
                         ┌──────────────────────────────┐
                         │          RED TEAM            │
                         │                              │
                         │  Identify Emerging Attacks  │
                         │              ↓               │
                         │  Generate Attack Scenarios  │
                         │              ↓               │
                         │  Synthetic Event Simulation │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │       BLUE TEAM DEFENSE      │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 1 — Rule Filter        │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 2 — XGBoost             │
                         │ Behavioral ML Detection       │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 3 — Graph Detector     │
                         │ GCN / Relationship Signals   │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 4 — Autoencoder        │
                         │ Anomaly Detection            │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 5 — Risk Fusion        │
                         │ Combine Detector Signals     │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 6 — Decision Policy    │
                         │ Risk → Action                │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Stage 7 — Explainability     │
                         │ SHAP + Case Reports          │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │      ADAPTIVE FEEDBACK       │
                         │                              │
                         │  Miss Collection             │
                         │          ↓                   │
                         │  Hard Example Generation     │
                         │          ↓                   │
                         │  Re-evaluation              │
                         │          ↓                   │
                         │  Defense Improvement        │
                         └──────────────────────────────┘
1. Identify — Emerging Fraud Attacks

The Red Team models emerging payment-fraud behavior using structured attack scenarios.

The simulator represents observable payment-system behavior including:

Session login
Device registration
Authentication failures
Beneficiary additions
Transactions
Transaction failures
Successful transactions
Channel changes
Behavioral timing
Account-access behavior
Account-modification behavior
Exploitation and persistence signals

The system separates:

Observable Evidence

Information that a real fraud detector would actually be able to observe.

Ground Truth

The simulated attack objective and scenario metadata.

This separation prevents hidden attack information from leaking into the detection model.

2. Generate — Synthetic Attack Simulation

The Red Team generation pipeline is:

Reference Data
      ↓
Statistical Calibration
      ↓
Normal Behavioral World
      ↓
Attack Signature Library
      ↓
Scenario Composition
      ↓
Simulation Engine
      ↓
Synthetic Attack Traces
      ↓
Realism / Novelty Validation

The simulator generates synthetic:

Entities
Events
Relationships
Sessions
Devices
Beneficiaries
Transactions
Attack scenarios

The generated traces are designed to resemble realistic behavioral patterns while remaining entirely synthetic.

The simulator does not interact with real payment infrastructure.

3. Statistical Calibration

The synthetic environment is calibrated using public reference datasets.

PaySim

PaySim is used for numerical transaction distributions and transaction-category mapping.

It provides a reference distribution for synthetic payment behavior.

IEEE-CIS Fraud Detection

IEEE-CIS Fraud Detection is used primarily for categorical and device-related distributions.

Because the public datasets do not contain every type of telemetry required for long-term payment-security modeling, some aspects of the environment are explicitly domain-modeled.

4. Provenance Model

Features are classified into three provenance tiers.

Tier 1 — Learned

Empirically learned directly from reference data.

Examples include:

Transaction amount distributions
Numerical transaction behavior
Observed categorical distributions
Tier 2 — Derived

Computed from reference features using explicit derivation rules.

Examples include:

Typical transaction amount
Aggregated behavioral statistics
Derived temporal features
Tier 3 — Domain Modeled

Synthetic assumptions used where suitable public telemetry is unavailable.

Examples include:

Long-term beneficiary relationships
Extended behavioral state
Certain relationship-level signals

This provenance system prevents domain assumptions from being incorrectly presented as directly observed real-world measurements.

5. Defend — Multi-Stage Detection

The Blue Team uses several complementary detection mechanisms.

The purpose is to combine:

Deterministic signals
Supervised machine learning
Graph relationships
Unsupervised anomaly detection
Risk fusion
Decision policy
Explainability
Stage 1 — Rule Filter

The first layer applies deterministic behavioral rules.

Its purpose is to provide a fast first-line defense for high-confidence patterns before more computationally expensive models are applied.

Conceptually:

Payment/Event
     ↓
Rule Evaluation
     ↓
Known High-Confidence Pattern?
     ↓
Yes → Flag
No  → Continue to ML Detection
6. Stage 2 — XGBoost Behavioral Detection

The primary tabular behavioral detector uses XGBoost over engineered event-sequence features.

The model captures behavioral patterns across synthetic payment activity.

Representative features include:

Transaction counts
Session-login counts
Device-registration counts
Beneficiary additions
Total events
Transactions per hour
Transactions per session
Authentication failures
New-device indicators
Beneficiary-before-transaction behavior
Failed transactions
Amount statistics
Amount trends
Channel diversity
Event timing

The model is calibrated before downstream policy decisions.

The verified trained model is preserved under:

blue_team_output_FROZEN/xgb_model.joblib
7. Stage 3 — Graph Detector

Payment-security behavior is not purely tabular.

Relationships between entities can contain important signals.

The graph detector models relationships between entities and events using graph-based representations.

Conceptually:

Customer
   │
   ├── Device
   │
   ├── Session
   │
   ├── Beneficiary
   │
   └── Transaction

The graph component provides structural information that may not be captured by a purely tabular classifier.

The corresponding verified results are stored in:

blue_team_output_FROZEN/gnn_results.json
8. Stage 4 — Autoencoder Anomaly Detection

The Autoencoder provides an independent anomaly-detection signal.

Instead of relying only on labeled fraud examples, it learns patterns associated with normal behavior.

Conceptually:

Normal Behavioral Data
          ↓
     Autoencoder
          ↓
Reconstruction Error
          ↓
  Anomaly Signal

This complements the supervised XGBoost model.

Verified results are preserved in:

blue_team_output_FROZEN/stage4_autoencoder_results.json
9. Stage 5 — Risk Fusion

The individual detector outputs are combined into a unified risk signal.

Rule Signal
     +
XGBoost Signal
     +
Graph Signal
     +
Autoencoder Signal
     ↓
Risk Fusion
     ↓
Unified Risk Score

The purpose of risk fusion is to combine different types of evidence rather than depending on a single detector.

Verified fusion outputs are preserved in:

blue_team_output_FROZEN/risk_fusion_results.json
10. Stage 6 — Decision Policy

The unified risk score is converted into an operational decision.

Conceptually:

                 Risk Score
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
     LOW RISK    MEDIUM RISK   HIGH RISK
        │            │            │
        ▼            ▼            ▼
      Allow      Verification   Block /
                  / Review      Escalate

The decision policy is intentionally separated from the underlying ML models.

This allows policy thresholds to be evaluated independently.

Policy results are stored in:

frozen_reports/decision_policy_results.json

Sensitivity analysis is stored in:

frozen_reports/decision_policy_sensitivity_results.json
11. Stage 7 — Explainability

The system provides both global and case-level explanations.

Global Explainability

SHAP analysis is used to identify features contributing to model behavior.

Artifacts:

blue_team_output_FROZEN/explainability/
├── global_feature_importance.json
└── global_shap_summary.png
Case-Level Explainability

Individual cases have structured explanation reports:

blue_team_output_FROZEN/explainability/
├── case_reports.json
└── case_reports.md

This allows the system to provide more than a simple:

Fraud = True

Instead, the system can expose the behavioral evidence contributing to the decision.

12. Adaptive Feedback Loop

One of the central ideas of the project is that detection failures should become future stress-testing data.

              Detection
                  ↓
            Miss Collection
                  ↓
            Failure Analysis
                  ↓
        Hard Example Generation
                  ↓
           Re-evaluation
                  ↓
        Defense Improvement
                  ↓
               Repeat

This creates a closed-loop adversarial defense system.

The Red Team generates attacks.

The Blue Team detects them.

The Blue Team's misses become information for future Red Team stress tests.

This creates an iterative:

Attack → Detect → Analyze → Stress-Test → Improve

cycle.

13. Hard Example Generation

Hard examples are generated from cases where the defense has difficulty distinguishing attack behavior.

The generated hard examples are stored in:

blue_team_output_FROZEN/hard_examples.jsonl

The generation report is stored in:

blue_team_output_FROZEN/hard_example_generation_report.json

These examples are intended for controlled evaluation and stress testing rather than real-world attack execution.

14. Verified Evaluation

The repository contains the verified outputs from the end-to-end evaluation.

The observed Round-1 and Round-2 ATO recall values were:

Evaluation	ATO Recall
Round 1	98.97%
Round 2	96.08%

The evaluation also included controlled analysis of the difference between the two rounds.

The investigation found:

Round 1 contained 97 ATO cases.
Round 2 contained 102 ATO cases.
None of the original 97 ATO cases flipped from correct to incorrect.
Three of the additional Round-2 misses were newly introduced hard examples.
Adding examples changed the StratifiedKFold partitioning.
A controlled same-fold evaluation produced 0/97 original ATO misses.

Therefore, the Round-2 recall difference should be interpreted in the context of changed sample composition and cross-validation fold assignment rather than being treated automatically as model degradation.

Detailed evidence is available in:

reports/FINAL_VALIDATION_REPORT.md
15. Hard-Example Diversity Investigation

The five generated ATO hard examples were investigated at the actual model-feature level.

Their provenance showed:

5 hard examples
       ↓
2 source misses

When passed through the real feature extractor:

25 / 26 features
        ↓
    identical

1 feature
        ↓
login → device-registration timing

Therefore, the five cases should not be described as five fully independent attack mechanisms.

They represent variations of a narrow minimal-trace ATO template.

This limitation is explicitly documented rather than hidden.

Detailed investigation:

reports/problem4_ato_hard_example_diversity_investigation.md

A future improvement is to generate hard examples from a broader set of independent source misses and attack mechanisms.

16. Validation

The current repository passes the complete test suite:

468 passed, 1 warning

Command:

python -m pytest -q

The remaining warning concerns shuffling an Arrow StringArray in:

tests/test_sequence_dataset.py

and:

src/red_team/ml/sequence_dataset.py

It does not currently cause a test failure.

17. Frozen Verified Artifacts

The verified Blue Team baseline is preserved under:

blue_team_output_FROZEN/

Important artifacts include:

blue_team_output_FROZEN/
├── calibrator.joblib
├── xgb_model.joblib
├── gnn_results.json
├── hard_example_generation_report.json
├── hard_examples.jsonl
├── misses.jsonl
├── results.json
├── risk_fusion_results.json
├── round1_vs_round2_report.json
├── stage4_autoencoder_results.json
├── three_stage_cascade_results.json
└── explainability/
    ├── case_reports.json
    ├── case_reports.md
    ├── global_feature_importance.json
    └── global_shap_summary.png

Additional adaptive-evaluation artifacts:

frozen_reports/
├── adaptive_eval_holdout.json
├── adaptive_round2_report.json
├── decision_policy_results.json
├── decision_policy_sensitivity_results.json
└── misses.jsonl

The verified baseline is tagged:

v1.0-frozen-verified

The purpose of the frozen directory is to preserve a reproducible verified baseline.

It does not mean that the system cannot be demonstrated through the web prototype.

18. Working Web Prototype

The project contains a browser-based prototype for demonstrating the system.

There are two components:

Streamlit UI
     ↓
FastAPI Backend
     ↓
Verified Pipeline Outputs
Streamlit Application

The Streamlit application is located at:

streamlit_app/app.py

Run locally:

streamlit run streamlit_app/app.py

The application provides the judge-facing demonstration interface.

FastAPI Backend

The backend is located at:

web_prototype/api/

Run locally:

$env:PYTHONPATH="$PWD\src"
python -m uvicorn web_prototype.api.app:app --reload --port 8000

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/api/health

Dashboard data:

http://127.0.0.1:8000/api/reports/dashboard

The API reads the project's actual reports and model outputs rather than presenting fabricated evaluation values.

19. Running the Complete Prototype Locally

Open Terminal 1:

cd "C:\Users\New\Downloads\AI_Defence_Sys-master (1)\AI_Defence_Sys-master"

$env:PYTHONPATH="$PWD\src"

python -m uvicorn web_prototype.api.app:app --reload --port 8000

Then open Terminal 2:

cd "C:\Users\New\Downloads\AI_Defence_Sys-master (1)\AI_Defence_Sys-master"

streamlit run streamlit_app/app.py

The Streamlit interface will normally open at:

http://localhost:8501

The backend will run at:

http://127.0.0.1:8000
20. Repository Structure
AI_Defence_Sys/
│
├── src/
│   └── red_team/
│       ├── ...
│       └── ...
│
├── tests/
│
├── scripts/
│
├── reports/
│   ├── FINAL_VALIDATION_REPORT.md
│   └── problem4_ato_hard_example_diversity_investigation.md
│
├── blue_team_output/
│
├── blue_team_output_FROZEN/
│   ├── xgb_model.joblib
│   ├── calibrator.joblib
│   ├── risk_fusion_results.json
│   ├── results.json
│   └── explainability/
│
├── frozen_reports/
│
├── web_prototype/
│   └── api/
│       ├── app.py
│       ├── config.py
│       ├── pipeline_runner.py
│       ├── reports.py
│       └── README.md
│
├── streamlit_app/
│   └── app.py
│
├── data/
│   └── reference/
│
├── models/
│
├── requirements.txt
├── .gitignore
├── README.md
├── DATASET_LICENSE.md
├── BLUE_TEAM_INTEGRATION_SPEC.md
├── RED_TEAM_HANDOFF.md
└── STAGE_STATUS.md
21. Installation

Clone the repository:

git clone https://github.com/Pranavi0525/AI_Defence_Sys.git
cd AI_Defence_Sys

Install dependencies:

pip install -r requirements.txt

Install the project with development dependencies:

pip install -e ".[dev]"

Set the Python source path:

Windows PowerShell
$env:PYTHONPATH="$PWD\src"
Linux / macOS
export PYTHONPATH="$PWD/src"
22. Run Tests

Run the complete test suite:

python -m pytest -q

Expected verified baseline:

468 passed, 1 warning

For verbose output:

pytest tests/ -v
23. Streamlit Deployment

The web prototype is designed to be deployable as a Streamlit application.

The recommended deployment architecture is:

GitHub Repository
        ↓
Streamlit Community Cloud
        ↓
Streamlit Application

The Streamlit entry point is:

streamlit_app/app.py

The repository should contain the dependency specification required by the Streamlit deployment environment.

For deployment, the Streamlit application should be configured to use repository-local artifacts and should not depend on:

127.0.0.1
localhost

for judge-facing functionality.

24. Real-World Feasibility

The architecture is designed around components that can conceptually be deployed in a real-time payment-security environment.

A production deployment could follow:

Payment Event
      ↓
Low-Latency Rule Filter
      ↓
Behavioral Feature Extraction
      ↓
ML Detection
      ↓
Graph / Relationship Signals
      ↓
Anomaly Detection
      ↓
Risk Fusion
      ↓
Decision Policy
      ↓
Allow / Verify / Review / Block

A production system would additionally require:

Real-time payment-stream integration
Low-latency model serving
Feature-store integration
Model monitoring
Data-drift monitoring
Adversarial monitoring
Human-review workflows
Security controls
Privacy controls
Governance
Regulatory compliance
Continuous validation
Model versioning
Audit logging

The current implementation is a controlled research prototype rather than a production payment-processing system.

25. Security and Safety Boundary

This project is a controlled payment-security research simulation.

The Red Team components generate synthetic scenarios only.

The project:

Does not access real banking systems.
Does not interact with payment networks.
Does not submit real payment requests.
Does not target real accounts.
Does not contain real customer payment information.
Uses synthetic entities and simulated events for research.

The objective is to improve fraud detection and resilience through controlled adversarial evaluation.

26. Known Limitations
Synthetic Data

The realism of generated data is bounded by the public datasets used for calibration.

Tail Behavior

Public datasets may not fully represent rare real-world fraud behavior.

Device Information

IEEE-CIS device information is hashed/obfuscated, limiting exact categorical recovery.

Long-Term Behavioral State

Long-term behavioral relationships are domain-modeled where suitable public telemetry is unavailable.

Hard-Example Diversity

The current five ATO hard examples are concentrated around two source misses and are highly similar in model feature space.

They should therefore be interpreted as variations of a narrow hard-example template rather than five independent attack families.

Evaluation Stability

Round-to-round comparisons can be affected by:

Sample-count changes
Cross-validation partitioning
Fold reassignment
Newly introduced hard examples

Future regression evaluation should use fixed evaluation sets and controlled fold assignments.

Production Deployment

The current project is a research prototype.

Production deployment would require additional:

Infrastructure
Security
Governance
Privacy
Compliance
Monitoring
Operational controls
27. Competition Alignment

The project directly maps to the three core pillars of the competition.

Competition Requirement	Project Component
Identify	Research-grounded attack signatures and structured scenarios
Generate	Synthetic attack generation and event simulation
Defend	Multi-stage ML defense pipeline
Detection efficacy	XGBoost + Graph Detector + Autoencoder + Risk Fusion
Mitigation	Decision Policy
Explainability	SHAP + Case-Level Reports
Adaptive Defense	Miss Collection + Hard Examples + Re-evaluation
Real-world feasibility	Layered detection and decision architecture
Working Prototype	Streamlit + FastAPI
Reproducibility	Automated tests + Frozen Verified Artifacts
28. Competition Requirement: Code Repository

The competition requires a complete, runnable GitHub repository covering:

Identify
Generate
Defend

This repository contains:

src/
tests/
scripts/
blue_team_output/
blue_team_output_FROZEN/
frozen_reports/
reports/
web_prototype/
streamlit_app/

The repository also contains reproducibility and validation artifacts.

29. Competition Requirement: Solution Walkthrough

The solution walkthrough should explain:

The emerging fraud attacks identified.
How synthetic attacks are generated.
How the simulation is calibrated.
How attack fidelity is evaluated.
How the Blue Team detects attacks.
How detector outputs are fused.
How decisions are made.
How decisions are explained.
How misses become hard examples.
How the system supports real-world payment-security deployment.

The walkthrough should be submitted as the required .docx artifact in the competition's Writeups section.

30. Competition Requirement: Working Web Prototype

The project provides a web-based prototype using:

Streamlit
    +
FastAPI

The Streamlit application acts as the judge-facing interface.

The FastAPI service exposes the underlying pipeline/report information.

The intended demonstration flow is:

Attack Identification
        ↓
Attack Generation
        ↓
Defense Pipeline
        ↓
Risk Score
        ↓
Decision
        ↓
Explanation
        ↓
Miss / Hard Example
        ↓
Adaptive Evaluation
31. Final Closed Loop

The central concept of the project can be summarized as:

                  ┌───────────────┐
                  │    IDENTIFY   │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │    GENERATE   │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │     DETECT    │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │      FUSE     │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │     DECIDE    │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │    EXPLAIN    │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │ FIND MISSES   │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │ HARD EXAMPLES │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │ RE-EVALUATE   │
                  └───────┬───────┘
                          │
                          └───────────────┐
                                          ↓
                                   STRENGTHEN DEFENSE
                                          │
                                          └──────→ REPEAT

The key idea is:

The attacks generated by the Red Team become the stress-testing ground for the Blue Team. The failures discovered by the Blue Team become feedback for the next evaluation cycle.

This transforms the system from a static fraud classifier into a closed-loop adversarial payment-security research platform.

32. Project Status
Red Team

FROZEN & QUALIFIED

See:

RED_TEAM_HANDOFF.md
Blue Team

IMPLEMENTED, EVALUATED & VERIFIED

Verified artifacts are preserved under:

blue_team_output_FROZEN/
frozen_reports/
Automated Tests
468 passed
1 warning
0 failures
Web Prototype
Streamlit + FastAPI
Verified Git Tag
v1.0-frozen-verified
License and Dataset Attribution

Dataset usage and licensing information is documented in:

DATASET_LICENSE.md

The project distinguishes public reference data from derived and synthetic data through its provenance model.
