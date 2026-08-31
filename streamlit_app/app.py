import json
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------
# AI Defense Lab — standalone Streamlit competition prototype
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="AI Defense Lab",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ROOT / "blue_team_output_FROZEN"
REPORTS = ROOT / "frozen_reports"
EXPLAIN = FROZEN / "explainability"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_jsonl(path: Path):
    rows = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return rows


def first_value(obj, names):
    """Recursively find the first useful value for any of the supplied keys."""
    if isinstance(obj, dict):
        for name in names:
            if name in obj and obj[name] not in (None, ""):
                return obj[name]
        for value in obj.values():
            found = first_value(value, names)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = first_value(value, names)
            if found not in (None, ""):
                return found
    return None


def numeric_value(obj, names):
    value = first_value(obj, names)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct(value):
    if value is None:
        return "—"
    if value <= 1:
        return f"{value * 100:.2f}%"
    return f"{value:.2f}%"


def metric_from_report(report, names):
    return numeric_value(report, names)


def existing(path):
    return path.exists()


# ---------------------------------------------------------------------
# Load frozen evidence
# ---------------------------------------------------------------------

results = load_json(FROZEN / "results.json")
cascade = load_json(FROZEN / "three_stage_cascade_results.json")
gnn = load_json(FROZEN / "gnn_results.json")
autoencoder = load_json(FROZEN / "stage4_autoencoder_results.json")
fusion = load_json(FROZEN / "risk_fusion_results.json")
decision = load_json(REPORTS / "decision_policy_results.json")
sensitivity = load_json(REPORTS / "decision_policy_sensitivity_results.json")
rounds = load_json(FROZEN / "round1_vs_round2_report.json")
adaptive = load_json(REPORTS / "adaptive_round2_report.json")
holdout = load_json(REPORTS / "adaptive_eval_holdout.json")
hard_generation = load_json(FROZEN / "hard_example_generation_report.json")

misses = load_jsonl(REPORTS / "misses.jsonl")
if not misses:
    misses = load_jsonl(FROZEN / "misses.jsonl")

hard_examples = load_jsonl(FROZEN / "hard_examples.jsonl")
cases = load_json(EXPLAIN / "case_reports.json")
feature_importance = load_json(EXPLAIN / "global_feature_importance.json")


# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------

st.markdown(
    """
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.15rem;
        color: #9aa4b2;
        margin-bottom: 1.5rem;
    }
    .stage-card {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        padding: 18px 12px;
        text-align: center;
        min-height: 125px;
        background: rgba(128,128,128,.06);
    }
    .stage-number {
        font-size: .78rem;
        color: #8b96a5;
        text-transform: uppercase;
        letter-spacing: .08em;
    }
    .stage-name {
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 7px;
    }
    .stage-desc {
        font-size: .78rem;
        color: #9aa4b2;
        margin-top: 5px;
    }
    .loop-box {
        border: 1px dashed rgba(128,128,128,.45);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🛡️ AI Defense Lab")
    st.caption("Competition prototype")

    page = st.radio(
        "Navigate",
        [
            "Executive Dashboard",
            "Red Team",
            "Blue Team",
            "Adaptive Defense",
            "Explainability",
            "Evidence",
        ],
    )

    st.divider()

    frozen_count = sum(
        [
            FROZEN.exists(),
            (FROZEN / "xgb_model.joblib").exists(),
            (FROZEN / "calibrator.joblib").exists(),
            (FROZEN / "hard_examples.jsonl").exists(),
            (EXPLAIN / "global_shap_summary.png").exists(),
        ]
    )

    st.caption("Frozen evidence")
    st.progress(frozen_count / 5)
    st.caption(f"{frozen_count}/5 key artifacts detected")

    if st.button("🔄 Refresh evidence", use_container_width=True):
        st.rerun()


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.markdown('<div class="main-title">🛡️ AI Defense Lab</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Red Team → Generate → Blue Team → Adaptive Defense</div>',
    unsafe_allow_html=True,
)

st.info(
    "Controlled synthetic payment-security research environment. "
    "The prototype reads the verified frozen evaluation artifacts and "
    "does not connect to real payment systems."
)


# ---------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------

st.subheader("Closed-Loop Defense Pipeline")

stages = [
    ("Stage 1", "Rule Filter", "Fast deterministic screening"),
    ("Stage 2", "XGBoost", "Behavioral ML detection"),
    ("Stage 3", "GCN", "Relationship / graph signals"),
    ("Stage 4", "Autoencoder", "Novelty / anomaly detection"),
    ("Stage 5", "Risk Fusion", "Unified risk score"),
    ("Stage 6", "Decision Policy", "Risk → action"),
    ("Stage 7", "Explainability", "SHAP + case reports"),
]

cols = st.columns(7)
for col, (num, name, desc) in zip(cols, stages):
    with col:
        st.markdown(
            f"""
            <div class="stage-card">
                <div class="stage-number">{num}</div>
                <div class="stage-name">{name}</div>
                <div class="stage-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="loop-box">
        <b>Adaptive Feedback Loop</b><br>
        Detection misses → Hard examples → Re-evaluation → Stronger defense
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Executive Dashboard
# ---------------------------------------------------------------------

if page == "Executive Dashboard":
    st.divider()
    st.subheader("Evaluation Snapshot")

    precision = metric_from_report(
        results, ["precision", "precision_score", "test_precision"]
    )
    recall = metric_from_report(
        results, ["recall", "recall_score", "test_recall", "sensitivity"]
    )
    f1 = metric_from_report(
        results, ["f1", "f1_score", "f1_macro", "test_f1"]
    )
    auc = metric_from_report(
        results, ["auc", "roc_auc", "roc_auc_score", "test_auc"]
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precision", pct(precision))
    m2.metric("Recall", pct(recall))
    m3.metric("F1", pct(f1))
    m4.metric("AUC", pct(auc))

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Defense Components")
        component_rows = []

        for label, obj in [
            ("XGBoost", results),
            ("GCN", gnn),
            ("Autoencoder", autoencoder),
            ("Risk Fusion", fusion),
            ("Decision Policy", decision),
        ]:
            component_rows.append(
                {
                    "Component": label,
                    "Status": "Available" if obj else "No report found",
                }
            )

        st.dataframe(
            pd.DataFrame(component_rows),
            hide_index=True,
            use_container_width=True,
        )

    with right:
        st.subheader("Closed-Loop Evidence")
        evidence_rows = [
            ("Attack generation", bool(hard_examples or hard_generation)),
            ("Detection misses", bool(misses)),
            ("Adaptive evaluation", bool(adaptive or holdout)),
            ("Decision policy", bool(decision)),
            ("SHAP explanation", (EXPLAIN / "global_shap_summary.png").exists()),
        ]
        st.dataframe(
            pd.DataFrame(
                [{"Evidence": a, "Present": "✓" if b else "—"} for a, b in evidence_rows]
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
    st.subheader("Round 1 → Round 2")

    if rounds:
        st.json(rounds)
    else:
        st.warning("Round comparison report was not found.")


# ---------------------------------------------------------------------
# Red Team
# ---------------------------------------------------------------------

elif page == "Red Team":
    st.header("🔴 Red Team — Attack Intelligence & Generation")

    st.write(
        "The Red Team identifies plausible emerging payment-fraud behaviors "
        "and converts them into controlled synthetic event traces for "
        "stress-testing the defense."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Hard examples", len(hard_examples))
    c2.metric("Observed misses", len(misses))
    c3.metric(
        "Generation report",
        "Available" if hard_generation else "Not found",
    )

    st.divider()

    st.subheader("Generated Attack Evidence")

    if hard_examples:
        df = pd.json_normalize(hard_examples)
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    else:
        st.info("No hard-example records were found in the frozen artifacts.")

    if hard_generation:
        with st.expander("Attack-generation validation report"):
            st.json(hard_generation)


# ---------------------------------------------------------------------
# Blue Team
# ---------------------------------------------------------------------

elif page == "Blue Team":
    st.header("🔵 Blue Team — Multi-Stage Detection")

    st.write(
        "The defense combines complementary signals rather than relying on "
        "a single classifier: behavioral ML, graph relationships, anomaly "
        "detection, risk fusion, and a decision policy."
    )

    tabs = st.tabs(
        [
            "XGBoost",
            "GCN",
            "Autoencoder",
            "Risk Fusion",
            "Decision Policy",
        ]
    )

    with tabs[0]:
        st.subheader("Stage 2 — XGBoost")
        st.caption("Behavioral machine-learning detector")
        if results:
            st.json(results)
        else:
            st.warning("XGBoost result report not found.")

    with tabs[1]:
        st.subheader("Stage 3 — GCN")
        st.caption("Relationship / graph-based signals")
        if gnn:
            st.json(gnn)
        else:
            st.warning("GCN result report not found.")

    with tabs[2]:
        st.subheader("Stage 4 — Autoencoder")
        st.caption("Anomaly / novelty signal")
        if autoencoder:
            st.json(autoencoder)
        else:
            st.warning("Autoencoder report not found.")

    with tabs[3]:
        st.subheader("Stage 5 — Risk Fusion")
        st.caption("Combines complementary detector outputs")
        if fusion:
            st.json(fusion)
        else:
            st.warning("Risk-fusion report not found.")

    with tabs[4]:
        st.subheader("Stage 6 — Decision Policy")
        st.caption("Maps risk into an operational response")
        if decision:
            st.json(decision)
        else:
            st.warning("Decision-policy report not found.")

        if sensitivity:
            with st.expander("Decision-policy sensitivity analysis"):
                st.json(sensitivity)


# ---------------------------------------------------------------------
# Adaptive Defense
# ---------------------------------------------------------------------

elif page == "Adaptive Defense":
    st.header("🔁 Adaptive Defense")

    st.write(
        "Detection failures are treated as feedback. Misses become hard "
        "examples for subsequent evaluation, creating the closed loop "
        "required by the challenge."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Miss records", len(misses))
    c2.metric("Hard examples", len(hard_examples))
    c3.metric(
        "Adaptive round",
        "Available" if adaptive else "Not found",
    )

    st.divider()

    if adaptive:
        st.subheader("Adaptive Round 2")
        st.json(adaptive)

    if holdout:
        with st.expander("Adaptive evaluation holdout"):
            st.json(holdout)

    if misses:
        st.subheader("Detection Misses")
        miss_df = pd.json_normalize(misses)
        st.dataframe(miss_df.head(100), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Explainability
# ---------------------------------------------------------------------

elif page == "Explainability":
    st.header("🔎 Explainability")

    st.write(
        "The final stage exposes global feature importance and case-level "
        "explanations so that a detection result can be inspected rather "
        "than treated as an opaque score."
    )

    shap_path = EXPLAIN / "global_shap_summary.png"

    if shap_path.exists():
        st.subheader("Global SHAP Summary")
        st.image(str(shap_path), use_container_width=True)
    else:
        st.warning("Global SHAP summary image was not found.")

    if feature_importance:
        st.subheader("Global Feature Importance")
        if isinstance(feature_importance, dict):
            try:
                items = []
                for key, value in feature_importance.items():
                    if isinstance(value, (int, float)):
                        items.append({"Feature": key, "Importance": value})
                if items:
                    df = pd.DataFrame(items).sort_values(
                        "Importance", ascending=False
                    )
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.json(feature_importance)
            except Exception:
                st.json(feature_importance)
        else:
            st.json(feature_importance)

    if cases:
        st.subheader("Case Reports")
        if isinstance(cases, list):
            case_df = pd.json_normalize(cases)
            st.dataframe(
                case_df.head(100),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.json(cases)


# ---------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------

elif page == "Evidence":
    st.header("📁 Frozen Evidence")

    st.write(
        "This page exposes the artifacts used by the prototype. The "
        "Streamlit application is intentionally read-only with respect "
        "to the frozen evaluation outputs."
    )

    files = [
        FROZEN / "results.json",
        FROZEN / "gnn_results.json",
        FROZEN / "stage4_autoencoder_results.json",
        FROZEN / "risk_fusion_results.json",
        FROZEN / "round1_vs_round2_report.json",
        FROZEN / "hard_example_generation_report.json",
        FROZEN / "hard_examples.jsonl",
        FROZEN / "xgb_model.joblib",
        FROZEN / "calibrator.joblib",
        REPORTS / "adaptive_eval_holdout.json",
        REPORTS / "adaptive_round2_report.json",
        REPORTS / "decision_policy_results.json",
        REPORTS / "decision_policy_sensitivity_results.json",
        REPORTS / "misses.jsonl",
        EXPLAIN / "global_feature_importance.json",
        EXPLAIN / "global_shap_summary.png",
        EXPLAIN / "case_reports.json",
        EXPLAIN / "case_reports.md",
    ]

    evidence = []
    for path in files:
        evidence.append(
            {
                "Artifact": str(path.relative_to(ROOT)),
                "Status": "✓ Present" if path.exists() else "— Missing",
                "Size": f"{path.stat().st_size:,} bytes" if path.exists() else "—",
            }
        )

    st.dataframe(
        pd.DataFrame(evidence),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("Repository / Prototype Architecture")
    st.code(
        """README.md
src/
tests/
blue_team_output_FROZEN/
frozen_reports/
reports/
web_prototype/
streamlit_app/
    app.py
""",
        language="text",
    )

    st.success(
        "Prototype mode: standalone Streamlit. "
        "No FastAPI backend is required."
    )
