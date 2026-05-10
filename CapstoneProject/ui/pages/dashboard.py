"""
FE-02: Dashboard — Overview of processed feedback and generated tickets.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from config.settings import OUTPUT_TICKETS_PATH, OUTPUT_METRICS_PATH


def render():
    st.header("Dashboard")

    # ── Metrics cards ──────────────────────────────────────────────
    if OUTPUT_METRICS_PATH.exists():
        df_metrics = pd.read_csv(OUTPUT_METRICS_PATH)
        if not df_metrics.empty:
            latest = df_metrics.iloc[-1]
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Processed", int(latest.get("total_processed", 0)))
            c2.metric("Bugs", int(latest.get("bugs_count", 0)))
            c3.metric("Features", int(latest.get("features_count", 0)))
            c4.metric("Avg Confidence", f"{latest.get('avg_confidence', 0):.0%}")
            c5.metric("Processing Time", f"{latest.get('processing_time_seconds', 0):.1f}s")
        else:
            st.info("No pipeline runs yet. Go to **Run Pipeline** to get started.")
            return
    else:
        st.info("No pipeline runs yet. Go to **Run Pipeline** to get started.")
        return

    st.divider()

    # ── Tickets table ──────────────────────────────────────────────
    if OUTPUT_TICKETS_PATH.exists():
        df_tickets = pd.read_csv(OUTPUT_TICKETS_PATH, dtype=str).fillna("")
        if not df_tickets.empty:
            # Category breakdown charts
            col_chart, col_priority = st.columns(2)
            with col_chart:
                st.subheader("By Category")
                cat_counts = df_tickets["category"].value_counts()
                st.bar_chart(cat_counts)
            with col_priority:
                st.subheader("By Priority")
                pri_counts = df_tickets["priority"].value_counts()
                st.bar_chart(pri_counts)

            st.divider()

            # Duplicate filter
            show_dupes = st.checkbox("Show duplicates", value=False)
            display_df = df_tickets
            if not show_dupes:
                display_df = df_tickets[df_tickets["is_duplicate"] != "True"]

            st.subheader(f"Generated Tickets ({len(display_df)})")
            st.dataframe(
                display_df[["source_id", "category", "priority", "title", "quality_score", "is_duplicate"]],
                use_container_width=True,
                hide_index=True,
            )

            # Expandable detail view
            selected = st.selectbox("View ticket details", display_df["source_id"].tolist(), index=None, placeholder="Select a ticket...")
            if selected:
                row = display_df[display_df["source_id"] == selected].iloc[0]
                st.markdown(f"### {row['title']}")
                st.markdown(f"**Category:** {row['category']} | **Priority:** {row['priority']} | **Quality:** {row['quality_score']}")
                st.markdown(f"**Description:** {row['description']}")
                if row.get("technical_details"):
                    st.markdown(f"**Technical Details:** {row['technical_details']}")
                if row.get("is_duplicate") == "True":
                    st.warning(f"Duplicate of: {row.get('duplicate_of', 'unknown')}")
    else:
        st.info("No tickets generated yet.")
