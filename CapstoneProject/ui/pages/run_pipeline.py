"""
FE-03: Pipeline Trigger UI — Upload CSVs and run the full pipeline.
"""

import streamlit as st
import pandas as pd
import traceback
from pathlib import Path

from config.settings import INPUT_REVIEWS_PATH, INPUT_EMAILS_PATH


def _execute_pipeline(status_placeholder):
    """Run the full pipeline, returning (n_items, elapsed, errors) or raising."""
    import uuid, time
    from config.database import init_db
    from config.vectorstore import load_product_docs
    from agents.csv_reader import csv_reader_agent
    from agents.classifier import classifier_agent
    from agents.bug_analyzer import bug_analyzer_agent
    from agents.feature_extractor import feature_extractor_agent
    from agents.ticket_creator import ticket_creator_agent
    from agents.quality_critic import quality_critic_agent
    from agents.pipeline import _save_outputs
    from agents.state import PipelineState

    status_placeholder.write("Initializing database and loading product docs into RAG...")
    init_db()
    doc_count = load_product_docs()
    status_placeholder.write(f"Loaded {doc_count} product doc chunks into RAG.")

    status_placeholder.write("Reading CSV files and storing feedback in RAG...")
    run_id = str(uuid.uuid4())[:8]
    state = PipelineState(
        feedback_items=[], current_index=0,
        processed_count=0, errors=[], run_id=run_id,
    )
    start_time = time.time()
    state["_start_time"] = start_time
    state = {**state, **csv_reader_agent(state)}
    n_items = len(state["feedback_items"])
    status_placeholder.write(f"Loaded **{n_items}** feedback items.")

    steps = [
        ("Classifying feedback...", classifier_agent),
        ("Analyzing bugs (with product docs RAG)...", bug_analyzer_agent),
        ("Extracting feature requests (with product docs RAG)...", feature_extractor_agent),
        ("Creating tickets (with duplicate detection RAG)...", ticket_creator_agent),
        ("Quality review...", quality_critic_agent),
        ("Saving outputs...", _save_outputs),
    ]

    for msg, agent_fn in steps:
        status_placeholder.write(msg)
        state = {**state, **agent_fn(state)}

    elapsed = time.time() - start_time
    errors = state.get("errors", [])
    return n_items, elapsed, errors


def render():
    st.header("Run Pipeline")

    st.markdown("Upload feedback CSV files or use the existing mock data, then run the analysis pipeline.")

    # ── File upload section ─────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("App Store Reviews")
        reviews_file = st.file_uploader(
            "Upload app_store_reviews.csv",
            type=["csv"],
            key="reviews_upload",
        )
        if reviews_file:
            INPUT_REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
            INPUT_REVIEWS_PATH.write_bytes(reviews_file.getvalue())
            st.success(f"Uploaded: {reviews_file.name}")

        if INPUT_REVIEWS_PATH.exists():
            df = pd.read_csv(INPUT_REVIEWS_PATH)
            st.caption(f"Current file: **{len(df)} rows**")
            with st.expander("Preview"):
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)
        else:
            st.warning("No reviews file found.")

    with col2:
        st.subheader("Support Emails")
        emails_file = st.file_uploader(
            "Upload support_emails.csv",
            type=["csv"],
            key="emails_upload",
        )
        if emails_file:
            INPUT_EMAILS_PATH.parent.mkdir(parents=True, exist_ok=True)
            INPUT_EMAILS_PATH.write_bytes(emails_file.getvalue())
            st.success(f"Uploaded: {emails_file.name}")

        if INPUT_EMAILS_PATH.exists():
            df = pd.read_csv(INPUT_EMAILS_PATH)
            st.caption(f"Current file: **{len(df)} rows**")
            with st.expander("Preview"):
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)
        else:
            st.warning("No emails file found.")

    st.divider()

    # ── Run pipeline ───────────────────────────────────────────────
    can_run = INPUT_REVIEWS_PATH.exists() or INPUT_EMAILS_PATH.exists()

    if not can_run:
        st.warning("Upload at least one CSV file to run the pipeline.")
        return

    if st.button("Run Analysis Pipeline", type="primary", use_container_width=True):
        with st.status("Running pipeline...", expanded=True) as status:
            try:
                n_items, elapsed, errors = _execute_pipeline(st)
                status.update(label=f"Pipeline complete! {n_items} items in {elapsed:.1f}s", state="complete")

                if errors:
                    with st.expander(f"Warnings / Errors ({len(errors)})", expanded=False):
                        for err in errors:
                            st.warning(err)

                st.success(f"Processed **{n_items}** feedback items. Go to **Dashboard** to see results.")
                st.balloons()

            except Exception as e:
                status.update(label="Pipeline failed!", state="error")
                st.error(f"Pipeline error: {e}")
                st.code(traceback.format_exc())
