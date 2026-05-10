"""
Structured logging that writes to both console and processing_log.csv.
"""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from config.settings import OUTPUT_LOG_PATH

LOG_CSV_FIELDS = ["timestamp", "agent_name", "source_id", "action", "details", "confidence"]


def _ensure_log_csv():
    """Create the CSV with headers if it doesn't exist."""
    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not OUTPUT_LOG_PATH.exists():
        with open(OUTPUT_LOG_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_CSV_FIELDS)
            writer.writeheader()


def log_to_csv(agent_name: str, source_id: str, action: str, details: str = "", confidence: float = 0.0):
    """Append a structured row to processing_log.csv."""
    _ensure_log_csv()
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "source_id": source_id,
        "action": action,
        "details": details,
        "confidence": confidence,
    }
    with open(OUTPUT_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_CSV_FIELDS)
        writer.writerow(row)


def get_logger(name: str) -> logging.Logger:
    """Return a console logger with a standard format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(name)-25s %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
