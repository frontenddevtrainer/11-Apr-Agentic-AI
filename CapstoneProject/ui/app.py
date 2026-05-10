"""
FE-01: Streamlit App — Main entry point with sidebar navigation.
Run with: streamlit run ui/app.py
"""

import streamlit as st
from pathlib import Path
import sys

# Ensure project root is on sys.path so config/agents imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="TaskFlow Pro — Feedback Analysis",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar Navigation ─────────────────────────────────────────────
PAGES = {
    "Dashboard": "pages.dashboard",
    "Run Pipeline": "pages.run_pipeline",
    "Manual Override": "pages.manual_override",
    "Analytics": "pages.analytics",
    "Processing Log": "pages.processing_log",
    "Configuration": "pages.configuration",
    "Product Docs": "pages.product_docs",
}

st.sidebar.title("TaskFlow Pro")
st.sidebar.caption("Intelligent Feedback Analysis")
st.sidebar.divider()
selection = st.sidebar.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

# ── Dynamic page loading ───────────────────────────────────────────
import importlib

module_name = PAGES[selection]
full_module = f"ui.{module_name}"
try:
    page_module = importlib.import_module(full_module)
    page_module.render()
except Exception as e:
    st.error(f"Failed to load page **{selection}**: {e}")
    st.exception(e)
