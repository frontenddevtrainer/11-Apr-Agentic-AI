"""
FE-06: Analytics — Processing statistics, accuracy, and performance metrics.
"""

import streamlit as st
import pandas as pd

from config.settings import OUTPUT_TICKETS_PATH, OUTPUT_METRICS_PATH


def render():
    st.header("Analytics")

    # ── Pipeline run history ───────────────────────────────────────
    if not OUTPUT_METRICS_PATH.exists():
        st.info("No pipeline runs yet. Go to **Run Pipeline** first.")
        return

    df_metrics = pd.read_csv(OUTPUT_METRICS_PATH)
    if df_metrics.empty:
        st.info("No metrics recorded yet.")
        return

    st.subheader("Pipeline Run History")
    st.dataframe(df_metrics, use_container_width=True, hide_index=True)

    st.divider()

    # ── Category distribution ──────────────────────────────────────
    latest = df_metrics.iloc[-1]
    st.subheader("Latest Run — Category Distribution")
    cat_data = pd.DataFrame({
        "Category": ["Bug", "Feature Request", "Praise", "Complaint", "Spam"],
        "Count": [
            int(latest.get("bugs_count", 0)),
            int(latest.get("features_count", 0)),
            int(latest.get("praise_count", 0)),
            int(latest.get("complaints_count", 0)),
            int(latest.get("spam_count", 0)),
        ],
    })
    st.bar_chart(cat_data.set_index("Category"))

    st.divider()

    # ── Ticket quality & confidence ────────────────────────────────
    if OUTPUT_TICKETS_PATH.exists():
        df_tickets = pd.read_csv(OUTPUT_TICKETS_PATH, dtype=str).fillna("")
        if not df_tickets.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Quality Score Distribution")
                quality_scores = pd.to_numeric(df_tickets["quality_score"], errors="coerce").dropna()
                if not quality_scores.empty:
                    st.bar_chart(quality_scores.value_counts(bins=5).sort_index())
                    st.metric("Average Quality", f"{quality_scores.mean():.2f}")
                else:
                    st.caption("No quality scores available.")

            with col2:
                st.subheader("Confidence Score Distribution")
                conf_scores = pd.to_numeric(df_tickets["confidence"], errors="coerce").dropna()
                if not conf_scores.empty:
                    st.bar_chart(conf_scores.value_counts(bins=5).sort_index())
                    st.metric("Average Confidence", f"{conf_scores.mean():.2f}")
                else:
                    st.caption("No confidence scores available.")

            st.divider()

            # Duplicate stats
            dupes = df_tickets[df_tickets["is_duplicate"] == "True"]
            st.subheader("Duplicate Detection")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Tickets", len(df_tickets))
            c2.metric("Unique Tickets", len(df_tickets) - len(dupes))
            c3.metric("Duplicates Found", len(dupes))

    # ── Performance over runs ──────────────────────────────────────
    if len(df_metrics) > 1:
        st.divider()
        st.subheader("Processing Time Across Runs")
        st.line_chart(df_metrics.set_index("run_id")["processing_time_seconds"])
