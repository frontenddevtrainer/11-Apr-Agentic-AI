"""
BE-10: LangGraph Orchestration
Wires all agents into a StateGraph with conditional routing.

Pipeline flow:
  csv_reader → classifier → route_by_category → ticket_creator → quality_critic → save_outputs
                              ├─ Bug → bug_analyzer ─────┤
                              ├─ Feature → feature_ext ──┤
                              └─ Other → (skip) ─────────┘
"""

import csv
import json
import time
import uuid
from pathlib import Path

from langgraph.graph import StateGraph, END

from agents.state import PipelineState
from agents.csv_reader import csv_reader_agent
from agents.classifier import classifier_agent
from agents.bug_analyzer import bug_analyzer_agent
from agents.feature_extractor import feature_extractor_agent
from agents.ticket_creator import ticket_creator_agent
from agents.quality_critic import quality_critic_agent
from config.settings import OUTPUT_TICKETS_PATH, OUTPUT_METRICS_PATH
from config.logger import get_logger, log_to_csv
from config.vectorstore import load_product_docs
from config.database import init_db, get_session, Ticket, Metric

logger = get_logger("pipeline")

TICKET_CSV_FIELDS = [
    "source_id", "source_type", "category", "priority", "title",
    "description", "technical_details", "component", "is_duplicate",
    "duplicate_of", "quality_score", "confidence",
]


def _stringify(value) -> str:
    """Convert dicts/lists to JSON strings for storage."""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value) if value else ""


def _save_outputs(state: PipelineState) -> dict:
    """Save generated tickets to CSV and SQLite; compute metrics."""
    items = state["feedback_items"]
    run_id = state.get("run_id", "unknown")
    start_time = state.get("_start_time", time.time())

    # ── Write generated_tickets.csv ────────────────────────────────
    OUTPUT_TICKETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_TICKETS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TICKET_CSV_FIELDS)
        writer.writeheader()
        for item in items:
            ticket = item.get("ticket", {})
            if not ticket.get("title"):
                continue
            writer.writerow({
                "source_id": item["source_id"],
                "source_type": item["source_type"],
                "category": item.get("category", ""),
                "priority": ticket.get("priority", item.get("priority", "")),
                "title": ticket.get("title", ""),
                "description": ticket.get("description", ""),
                "technical_details": _stringify(ticket.get("technical_details", "")),
                "component": _stringify(ticket.get("component", "")),
                "is_duplicate": ticket.get("is_duplicate", False),
                "duplicate_of": ticket.get("duplicate_of", ""),
                "quality_score": item.get("quality_score", ""),
                "confidence": item.get("confidence", ""),
            })

    # ── Write to SQLite ────────────────────────────────────────────
    session = get_session()
    try:
        for item in items:
            ticket = item.get("ticket", {})
            if not ticket.get("title"):
                continue
            db_ticket = Ticket(
                source_id=item["source_id"],
                source_type=item["source_type"],
                category=item.get("category", ""),
                priority=ticket.get("priority", item.get("priority", "")),
                title=ticket.get("title", ""),
                description=ticket.get("description", ""),
                technical_details=_stringify(ticket.get("technical_details", "")),
                confidence_score=item.get("confidence", 0.0),
                status="open",
            )
            session.add(db_ticket)
        session.commit()
    finally:
        session.close()

    # ── Compute and save metrics ───────────────────────────────────
    categories = [item.get("category", "") for item in items]
    confidences = [item.get("confidence", 0.0) for item in items if item.get("confidence")]
    processing_time = time.time() - start_time

    metrics = {
        "run_id": run_id,
        "total_processed": len(items),
        "bugs_count": categories.count("Bug"),
        "features_count": categories.count("Feature Request"),
        "praise_count": categories.count("Praise"),
        "complaints_count": categories.count("Complaint"),
        "spam_count": categories.count("Spam"),
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "processing_time_seconds": round(processing_time, 2),
    }

    # Write metrics.csv
    OUTPUT_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = OUTPUT_METRICS_PATH.exists()
    with open(OUTPUT_METRICS_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(metrics)

    # Write metrics to SQLite
    session = get_session()
    try:
        db_metric = Metric(
            run_id=run_id,
            total_processed=metrics["total_processed"],
            bugs_count=metrics["bugs_count"],
            features_count=metrics["features_count"],
            praise_count=metrics["praise_count"],
            complaints_count=metrics["complaints_count"],
            spam_count=metrics["spam_count"],
            avg_confidence=metrics["avg_confidence"],
            processing_time_seconds=metrics["processing_time_seconds"],
        )
        session.add(db_metric)
        session.commit()
    finally:
        session.close()

    logger.info(
        "Pipeline complete: %d items processed in %.1fs (Bugs=%d, Features=%d, Praise=%d, Complaints=%d, Spam=%d)",
        metrics["total_processed"], processing_time,
        metrics["bugs_count"], metrics["features_count"],
        metrics["praise_count"], metrics["complaints_count"], metrics["spam_count"],
    )

    return {"processed_count": metrics["total_processed"]}


def build_pipeline() -> StateGraph:
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("csv_reader", csv_reader_agent)
    graph.add_node("classifier", classifier_agent)
    graph.add_node("bug_analyzer", bug_analyzer_agent)
    graph.add_node("feature_extractor", feature_extractor_agent)
    graph.add_node("ticket_creator", ticket_creator_agent)
    graph.add_node("quality_critic", quality_critic_agent)
    graph.add_node("save_outputs", _save_outputs)

    # Define edges
    graph.set_entry_point("csv_reader")
    graph.add_edge("csv_reader", "classifier")
    # After classification, run both specialist agents (they skip non-matching items)
    graph.add_edge("classifier", "bug_analyzer")
    graph.add_edge("bug_analyzer", "feature_extractor")
    graph.add_edge("feature_extractor", "ticket_creator")
    graph.add_edge("ticket_creator", "quality_critic")
    graph.add_edge("quality_critic", "save_outputs")
    graph.add_edge("save_outputs", END)

    return graph.compile()


def run_pipeline() -> dict:
    """Execute the full pipeline end-to-end."""
    # Ensure DB tables exist
    init_db()

    # Load product docs into RAG
    doc_count = load_product_docs()
    logger.info("Loaded %d product doc chunks into RAG", doc_count)

    # Build and run
    pipeline = build_pipeline()
    run_id = str(uuid.uuid4())[:8]
    initial_state = PipelineState(
        feedback_items=[],
        current_index=0,
        processed_count=0,
        errors=[],
        run_id=run_id,
    )
    initial_state["_start_time"] = time.time()

    logger.info("Starting pipeline run %s", run_id)
    result = pipeline.invoke(initial_state)
    return result


if __name__ == "__main__":
    run_pipeline()
