"""
FE-05: Manual Override — Edit or approve generated tickets.
"""

import streamlit as st
import pandas as pd

from config.settings import OUTPUT_TICKETS_PATH, CATEGORIES, PRIORITIES


def render():
    st.header("Manual Override")

    if not OUTPUT_TICKETS_PATH.exists():
        st.info("No tickets generated yet. Run the pipeline first.")
        return

    df = pd.read_csv(OUTPUT_TICKETS_PATH, dtype=str).fillna("")
    if df.empty:
        st.info("No tickets to display.")
        return

    st.markdown(f"**{len(df)} tickets** available for review. Edit fields below and save.")

    # ── Filter controls ────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    cat_filter = col_f1.multiselect("Filter by category", CATEGORIES, default=CATEGORIES)
    pri_filter = col_f2.multiselect("Filter by priority", PRIORITIES, default=PRIORITIES)

    filtered = df[df["category"].isin(cat_filter) & df["priority"].isin(pri_filter)]
    st.caption(f"Showing {len(filtered)} of {len(df)} tickets")

    st.divider()

    # ── Editable ticket list ───────────────────────────────────────
    edited_rows = []
    for idx, row in filtered.iterrows():
        with st.expander(f"[{row['source_id']}] {row['title']}", expanded=False):
            c1, c2 = st.columns(2)
            new_title = st.text_input("Title", value=row["title"], key=f"title_{idx}")
            new_cat = c1.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row["category"]) if row["category"] in CATEGORIES else 0, key=f"cat_{idx}")
            new_pri = c2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(row["priority"]) if row["priority"] in PRIORITIES else 0, key=f"pri_{idx}")
            new_desc = st.text_area("Description", value=row["description"], key=f"desc_{idx}", height=100)
            new_tech = st.text_input("Technical Details", value=row.get("technical_details", ""), key=f"tech_{idx}")

            edited_rows.append({
                "idx": idx,
                "title": new_title,
                "category": new_cat,
                "priority": new_pri,
                "description": new_desc,
                "technical_details": new_tech,
            })

    st.divider()

    if st.button("Save All Changes", type="primary", use_container_width=True):
        for edit in edited_rows:
            i = edit["idx"]
            df.at[i, "title"] = edit["title"]
            df.at[i, "category"] = edit["category"]
            df.at[i, "priority"] = edit["priority"]
            df.at[i, "description"] = edit["description"]
            df.at[i, "technical_details"] = edit["technical_details"]
        df.to_csv(OUTPUT_TICKETS_PATH, index=False)
        st.success(f"Saved {len(edited_rows)} ticket(s) to {OUTPUT_TICKETS_PATH.name}")
        st.rerun()
