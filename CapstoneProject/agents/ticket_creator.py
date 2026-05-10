"""
BE-08: Ticket Creator Agent
Generates structured tickets for actionable items (Bug, Feature Request,
Complaint). Uses RAG to detect duplicate tickets before creating new ones.
Stores each new ticket in the ticket RAG collection.
"""

import json

from agents.llm import get_llm, parse_llm_json
from agents.state import PipelineState
from config.logger import get_logger, log_to_csv
from config.vectorstore import (
    get_ticket_collection,
    get_feedback_collection,
    upsert_documents,
    query_similar,
)

logger = get_logger("ticket_creator_agent")

TICKET_PROMPT = """You are a project manager creating a structured ticket from user feedback for TaskFlow Pro.

## Feedback
Source ID: {source_id}
Source type: {source_type}
Category: {category}
Platform: {platform}
Rating: {rating}
Subject: {subject}
Text:
{text}

## Additional Analysis
{analysis_details}

## Similar Existing Tickets (from RAG — may be duplicates)
{similar_tickets}

---
Create a structured ticket. If this is very similar to an existing ticket above, mark it as a duplicate.
Respond ONLY with valid JSON:
{{
  "title": "<clear, actionable ticket title>",
  "description": "<detailed description including user impact>",
  "category": "{category}",
  "priority": "{priority}",
  "technical_details": "<device, OS, steps to reproduce, or N/A>",
  "component": "<affected component>",
  "is_duplicate": <true|false>,
  "duplicate_of": "<source_id of original if duplicate, else null>"
}}
"""

ACTIONABLE_CATEGORIES = {"Bug", "Feature Request", "Complaint"}


def ticket_creator_agent(state: PipelineState) -> dict:
    """Create tickets for actionable items with duplicate detection."""
    llm = get_llm(temperature=0.0)
    items = state["feedback_items"]
    errors = list(state.get("errors", []))
    ticket_col = get_ticket_collection()
    feedback_col = get_feedback_collection()

    for item in items:
        if item.get("category") not in ACTIONABLE_CATEGORIES:
            item["ticket"] = {}
            continue

        try:
            # ── RAG: check for duplicate/similar feedback ──────────
            query_text = f"{item.get('subject', '')} {item['text']}"
            similar_feedback = query_similar(feedback_col, query_text, n_results=5)
            similar_tickets_result = query_similar(ticket_col, query_text, n_results=3)

            # Format similar items for prompt (exclude self)
            similar_lines = []
            if similar_feedback["ids"][0]:
                for sid, doc, dist in zip(
                    similar_feedback["ids"][0],
                    similar_feedback["documents"][0],
                    similar_feedback["distances"][0],
                ):
                    if sid != item["source_id"] and dist < 1.0:
                        similar_lines.append(f"- [{sid}] (distance={dist:.2f}): {doc[:150]}")

            if similar_tickets_result["ids"][0]:
                for sid, doc, dist in zip(
                    similar_tickets_result["ids"][0],
                    similar_tickets_result["documents"][0],
                    similar_tickets_result["distances"][0],
                ):
                    if dist < 1.0:
                        similar_lines.append(f"- [TICKET:{sid}] (distance={dist:.2f}): {doc[:150]}")

            similar_text = "\n".join(similar_lines) if similar_lines else "No similar tickets found."
            item["similar_tickets"] = [s.split("]")[0].lstrip("- [") for s in similar_lines]

            # ── Build analysis context ─────────────────────────────
            analysis_parts = []
            if item.get("bug_details"):
                analysis_parts.append(f"Bug Analysis: {json.dumps(item['bug_details'])}")
            if item.get("feature_details"):
                analysis_parts.append(f"Feature Analysis: {json.dumps(item['feature_details'])}")
            analysis_details = "\n".join(analysis_parts) if analysis_parts else "No additional analysis."

            priority = item.get("priority", "Medium")

            prompt = TICKET_PROMPT.format(
                source_id=item["source_id"],
                source_type=item["source_type"],
                category=item["category"],
                platform=item.get("platform", ""),
                rating=item.get("rating", "N/A"),
                subject=item.get("subject", ""),
                text=item["text"],
                analysis_details=analysis_details,
                similar_tickets=similar_text,
                priority=priority,
            )
            response = llm.invoke(prompt)
            ticket = parse_llm_json(response.content)
            item["ticket"] = ticket

            if ticket.get("is_duplicate"):
                item["duplicate_of"] = ticket.get("duplicate_of", "")
                log_to_csv("ticket_creator", item["source_id"], "duplicate_detected",
                           f"duplicate_of={item['duplicate_of']}")
                logger.info("%s → DUPLICATE of %s", item["source_id"], item["duplicate_of"])
            else:
                # Store new ticket in RAG for future duplicate detection
                ticket_text = f"{ticket['title']} {ticket['description']}"
                upsert_documents(
                    ticket_col,
                    ids=[item["source_id"]],
                    documents=[ticket_text],
                    metadatas=[{
                        "source_id": item["source_id"],
                        "category": item["category"],
                        "priority": ticket.get("priority", priority),
                    }],
                )
                log_to_csv("ticket_creator", item["source_id"], "ticket_created",
                           f"title={ticket['title']}", item.get("confidence", 0.0))
                logger.info("%s → ticket: %s", item["source_id"], ticket["title"])

        except Exception as e:
            msg = f"Ticket creation error for {item['source_id']}: {e}"
            logger.error(msg)
            errors.append(msg)
            item["ticket"] = {}

    return {"feedback_items": items, "errors": errors}
