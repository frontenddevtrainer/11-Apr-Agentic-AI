"""
FE-08: Product Docs — Upload and manage technical documentation for RAG.
"""

import streamlit as st
from pathlib import Path

from config.settings import PRODUCT_DOCS_DIR
from config.vectorstore import load_product_docs, get_product_docs_collection


def render():
    st.header("Product Documentation")
    st.markdown(
        "Upload technical documentation (`.md` files) so the Bug Analyzer "
        "and Feature Extractor agents can use them as RAG context."
    )

    PRODUCT_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Upload section ──────────────────────────────────────────────
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload Markdown files",
        type=["md", "txt"],
        accept_multiple_files=True,
        key="doc_upload",
    )

    if uploaded_files:
        for f in uploaded_files:
            dest = PRODUCT_DOCS_DIR / f.name
            dest.write_bytes(f.getvalue())
            st.success(f"Saved: {f.name}")

        if st.button("Re-index Documents into RAG", type="primary"):
            with st.spinner("Indexing documents into ChromaDB..."):
                count = load_product_docs()
            st.success(f"Indexed **{count}** chunks into the product docs RAG collection.")

    st.divider()

    # ── Current documents ───────────────────────────────────────────
    st.subheader("Current Documents")
    md_files = sorted(PRODUCT_DOCS_DIR.glob("*.md")) + sorted(PRODUCT_DOCS_DIR.glob("*.txt"))

    if not md_files:
        st.info("No documents found. Upload some above.")
        return

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        col1, col2 = st.columns([5, 1])
        col1.markdown(f"**{md_file.name}** — {len(content):,} chars")
        if col2.button("Delete", key=f"del_{md_file.name}"):
            md_file.unlink()
            st.rerun()

        with st.expander(f"Preview: {md_file.name}", expanded=False):
            st.markdown(content[:3000])
            if len(content) > 3000:
                st.caption(f"... ({len(content) - 3000:,} more characters)")

    st.divider()

    # ── RAG collection stats ────────────────────────────────────────
    st.subheader("RAG Collection Status")
    collection = get_product_docs_collection()
    chunk_count = collection.count()
    st.metric("Chunks in ChromaDB", chunk_count)

    if chunk_count == 0:
        st.warning("No documents indexed. Upload files and click **Re-index**.")
    else:
        st.success(f"{chunk_count} chunks available for Bug Analyzer and Feature Extractor agents.")

    if st.button("Re-index All Documents"):
        with st.spinner("Re-indexing..."):
            count = load_product_docs()
        st.success(f"Re-indexed **{count}** chunks.")
        st.rerun()
