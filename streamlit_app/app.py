import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="AI Defense Lab",
    page_icon="???",
    layout="wide"
)

API = st.sidebar.text_input(
    "Backend API",
    "http://127.0.0.1:8000"
)

st.title("??? AI Defense Lab")
st.caption("Red Team ? Generate ? Blue Team ? Adaptive Defense")

if st.button("?? Refresh"):
    st.rerun()

try:
    health = requests.get(f"{API}/api/health", timeout=5)
    dashboard = requests.get(
        f"{API}/api/reports/dashboard",
        timeout=10
    )

    health.raise_for_status()
    dashboard.raise_for_status()

    data = dashboard.json()

    st.success("Backend connected")

    st.header("Defense Pipeline")

    stages = [
        ("Stage 1", "Rule Filter"),
        ("Stage 2", "XGBoost"),
        ("Stage 3", "GCN"),
        ("Stage 4", "Autoencoder"),
        ("Stage 5", "Risk Fusion"),
        ("Stage 6", "Decision Policy"),
        ("Stage 7", "Explainability"),
    ]

    cols = st.columns(len(stages))

    for col, (number, name) in zip(cols, stages):
        with col:
            st.metric(number, name)

    st.divider()

    st.header("System Results")

    st.json(data)

except Exception as e:
    st.error(f"Could not connect to backend: {e}")
    st.info(
        "Make sure FastAPI is running on "
        "http://127.0.0.1:8000"
    )
