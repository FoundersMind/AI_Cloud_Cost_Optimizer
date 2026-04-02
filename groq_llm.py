"""Groq Chat Completions — used by profile, billing, and analysis steps."""
from __future__ import annotations

import os
from typing import Any, Dict, List

# Override with GROQ_MODEL in .env (see https://console.groq.com/docs/models )
_DEFAULT_MODEL = "llama-3.3-70b-versatile"


def default_model() -> str:
    return (os.getenv("GROQ_MODEL") or _DEFAULT_MODEL).strip()


def chat_completion(
    messages: List[Dict[str, Any]],
    *,
    max_tokens: int,
    temperature: float = 0.25,
) -> str:
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to .env next to the Python scripts."
        )
    try:
        from groq import Groq
    except ImportError as e:
        raise RuntimeError("Install the Groq SDK: pip install groq") from e

    client = Groq(api_key=api_key)
    cleaned: List[Dict[str, str]] = []
    for m in messages:
        role = str(m.get("role", "user"))
        content = m.get("content", "")
        cleaned.append(
            {"role": role, "content": content if isinstance(content, str) else str(content)}
        )

    completion = client.chat.completions.create(
        model=default_model(),
        messages=cleaned,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if not completion.choices:
        return ""
    msg = completion.choices[0].message
    return (msg.content or "").strip()
