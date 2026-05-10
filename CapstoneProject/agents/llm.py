"""
Shared LLM instance using OpenAI via LangChain.
"""

import json
import re

from langchain_openai import ChatOpenAI
from config.settings import LLM_MODEL_NAME, OPENAI_API_KEY


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL_NAME,
        temperature=temperature,
        api_key=OPENAI_API_KEY,
    )


def parse_llm_json(text: str) -> dict:
    """Extract and parse JSON from LLM response, handling markdown code fences."""
    # Strip markdown code fences like ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)
