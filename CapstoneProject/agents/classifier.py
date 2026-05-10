"""
BE-05: Feedback Classifier Agent
Classifies each feedback item into Bug / Feature Request / Praise /
Complaint / Spam with a confidence score using OpenAI.
"""

from agents.llm import get_llm, parse_llm_json
from agents.state import PipelineState
from config.logger import get_logger, log_to_csv
from config.settings import CATEGORIES

logger = get_logger("classifier_agent")

CLASSIFIER_PROMPT = """You are a feedback classifier for a productivity app called TaskFlow Pro.

Classify the following user feedback into exactly ONE of these categories:
{categories}

Also assign a confidence score between 0.0 and 1.0.

Respond ONLY with valid JSON:
{{"category": "<category>", "confidence": <float>}}

---
Source type: {source_type}
Platform: {platform}
Rating: {rating}
Subject: {subject}
Feedback text:
{text}
"""


def classifier_agent(state: PipelineState) -> dict:
    """Classify every feedback item in state."""
    llm = get_llm(temperature=0.0)
    items = state["feedback_items"]
    errors = list(state.get("errors", []))

    for item in items:
        try:
            prompt = CLASSIFIER_PROMPT.format(
                categories=", ".join(CATEGORIES),
                source_type=item["source_type"],
                platform=item.get("platform", ""),
                rating=item.get("rating", "N/A"),
                subject=item.get("subject", ""),
                text=item["text"],
            )
            response = llm.invoke(prompt)
            result = parse_llm_json(response.content)

            category = result["category"]
            if category not in CATEGORIES:
                category = "Complaint"  # fallback

            item["category"] = category
            item["confidence"] = float(result["confidence"])

            log_to_csv(
                "classifier", item["source_id"], "classified",
                f"category={category}", item["confidence"],
            )
            logger.info("%s → %s (%.2f)", item["source_id"], category, item["confidence"])

        except Exception as e:
            msg = f"Classification error for {item['source_id']}: {e}"
            logger.error(msg)
            errors.append(msg)
            item["category"] = "Complaint"
            item["confidence"] = 0.0

    return {"feedback_items": items, "errors": errors}
