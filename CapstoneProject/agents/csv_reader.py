"""
BE-04: CSV Reader Agent
Reads app_store_reviews.csv and support_emails.csv, normalises into
a unified FeedbackItem list, and stores all feedback in RAG for
duplicate detection.
"""

import pandas as pd

from agents.state import FeedbackItem, PipelineState
from config.settings import INPUT_REVIEWS_PATH, INPUT_EMAILS_PATH
from config.logger import get_logger, log_to_csv
from config.vectorstore import get_feedback_collection, upsert_documents

logger = get_logger("csv_reader_agent")


def csv_reader_agent(state: PipelineState) -> dict:
    """Read CSVs and produce a list of FeedbackItem dicts."""
    items: list[FeedbackItem] = []
    errors: list[str] = list(state.get("errors", []))

    # ── App store reviews ──────────────────────────────────────────
    try:
        df_reviews = pd.read_csv(INPUT_REVIEWS_PATH, dtype=str).fillna("")
        for _, row in df_reviews.iterrows():
            items.append(FeedbackItem(
                source_id=row["review_id"],
                source_type="app_review",
                text=row["review_text"],
                subject="",
                platform=row.get("platform", ""),
                rating=int(row.get("rating", 0) or 0),
                user_name=row.get("user_name", ""),
                date=row.get("date", ""),
                app_version=row.get("app_version", ""),
                original_priority="",
            ))
        logger.info("Loaded %d app store reviews", len(df_reviews))
    except Exception as e:
        msg = f"Error reading reviews CSV: {e}"
        logger.error(msg)
        errors.append(msg)

    # ── Support emails ─────────────────────────────────────────────
    try:
        df_emails = pd.read_csv(INPUT_EMAILS_PATH, dtype=str).fillna("")
        for _, row in df_emails.iterrows():
            items.append(FeedbackItem(
                source_id=row["email_id"],
                source_type="support_email",
                text=row["body"],
                subject=row.get("subject", ""),
                platform="Email",
                rating=0,
                user_name=row.get("sender_email", ""),
                date=row.get("timestamp", ""),
                app_version="",
                original_priority=row.get("priority", ""),
            ))
        logger.info("Loaded %d support emails", len(df_emails))
    except Exception as e:
        msg = f"Error reading emails CSV: {e}"
        logger.error(msg)
        errors.append(msg)

    # ── Store all feedback in RAG for duplicate detection ──────────
    if items:
        fb_collection = get_feedback_collection()
        ids = [item["source_id"] for item in items]
        docs = [f"{item.get('subject', '')} {item['text']}" for item in items]
        metas = [{"source_type": item["source_type"], "source_id": item["source_id"]} for item in items]
        upsert_documents(fb_collection, ids, docs, metas)
        logger.info("Stored %d feedback items in RAG", len(items))

    for item in items:
        log_to_csv("csv_reader", item["source_id"], "loaded", f"source_type={item['source_type']}")

    return {
        "feedback_items": items,
        "processed_count": 0,
        "errors": errors,
    }
