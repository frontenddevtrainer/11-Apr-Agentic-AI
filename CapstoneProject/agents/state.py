"""
Shared state schema for the LangGraph pipeline.
Every agent reads from / writes to this TypedDict.
"""

from __future__ import annotations
from typing import TypedDict


class FeedbackItem(TypedDict, total=False):
    source_id: str
    source_type: str          # "app_review" or "support_email"
    text: str                 # review_text or email body
    subject: str              # email subject (empty for reviews)
    platform: str             # "Google Play", "App Store", or "Email"
    rating: int               # 1-5 for reviews, 0 for emails
    user_name: str
    date: str
    app_version: str
    original_priority: str    # from email CSV, if any
    # Populated by agents:
    category: str             # Bug, Feature Request, Praise, Complaint, Spam
    confidence: float
    priority: str             # Critical, High, Medium, Low
    bug_details: dict         # steps_to_reproduce, device, os, severity
    feature_details: dict     # summary, impact_score, user_segment
    ticket: dict              # title, description, technical_details, ...
    quality_score: float
    quality_notes: str
    duplicate_of: str         # source_id of duplicate, if any
    similar_tickets: list     # list of similar ticket IDs from RAG


class PipelineState(TypedDict, total=False):
    feedback_items: list[FeedbackItem]
    current_index: int
    processed_count: int
    errors: list[str]
    run_id: str
