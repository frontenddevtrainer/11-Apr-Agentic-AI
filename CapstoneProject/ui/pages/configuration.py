"""
FE-04: Configuration Panel — Adjust thresholds, model, and priority mappings.
"""

import streamlit as st
from pathlib import Path

from config.settings import PROJECT_ROOT


def _read_env() -> dict:
    """Parse the .env file into a dict."""
    env_path = PROJECT_ROOT / ".env"
    values = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                values[key.strip()] = val.strip()
    return values


def _write_env(values: dict):
    """Rewrite .env preserving comments and updating values."""
    env_path = PROJECT_ROOT / ".env"
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    new_lines = []
    written_keys = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in values:
                new_lines.append(f"{key}={values[key]}")
                written_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    # Append any new keys not in original file
    for key, val in values.items():
        if key not in written_keys:
            new_lines.append(f"{key}={val}")
    env_path.write_text("\n".join(new_lines) + "\n")


def render():
    st.header("Configuration")
    st.markdown("Adjust pipeline settings. Changes are saved to `.env` and take effect on the next pipeline run.")

    env = _read_env()

    # ── Model settings ─────────────────────────────────────────────
    st.subheader("LLM Model")
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"].index(
            env.get("LLM_MODEL_NAME", "gpt-4o-mini")
        ),
    )

    api_key = st.text_input(
        "OpenAI API Key",
        value=env.get("OPENAI_API_KEY", ""),
        type="password",
    )

    st.divider()

    # ── Classification settings ────────────────────────────────────
    st.subheader("Classification Thresholds")
    confidence = st.slider(
        "Minimum confidence threshold",
        0.0, 1.0,
        float(env.get("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7")),
        0.05,
        help="Items below this threshold will be flagged for manual review.",
    )

    st.divider()

    # ── Priority rating thresholds ─────────────────────────────────
    st.subheader("Priority Mapping (Rating Thresholds)")
    col1, col2, col3 = st.columns(3)
    critical_t = col1.number_input("Critical (rating <=)", value=int(env.get("CRITICAL_RATING_THRESHOLD", "1")), min_value=1, max_value=5)
    high_t = col2.number_input("High (rating <=)", value=int(env.get("HIGH_RATING_THRESHOLD", "2")), min_value=1, max_value=5)
    medium_t = col3.number_input("Medium (rating <=)", value=int(env.get("MEDIUM_RATING_THRESHOLD", "3")), min_value=1, max_value=5)

    st.divider()

    # ── Save ───────────────────────────────────────────────────────
    if st.button("Save Configuration", type="primary"):
        updates = {
            "LLM_MODEL_NAME": model,
            "OPENAI_API_KEY": api_key,
            "CLASSIFICATION_CONFIDENCE_THRESHOLD": str(confidence),
            "CRITICAL_RATING_THRESHOLD": str(critical_t),
            "HIGH_RATING_THRESHOLD": str(high_t),
            "MEDIUM_RATING_THRESHOLD": str(medium_t),
        }
        _write_env(updates)
        st.success("Configuration saved! Changes will apply on the next pipeline run.")
        st.info("Note: You may need to restart the Streamlit app for some settings to take effect.")
