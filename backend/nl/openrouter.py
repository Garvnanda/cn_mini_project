"""OpenRouter client: asks an LLM to fill the DesignInput JSON. It extracts facts only (D-004).

UNVERIFIED: written against the OpenRouter chat-completions API (OpenAI-compatible
`/api/v1/chat/completions`, `response_format: {"type": "json_object"}`); not yet run with a real key.
"""

import json
import os

import httpx

from engine.models import DesignInput

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/auto"  # UNVERIFIED default; set OPENROUTER_MODEL to pin one
TIMEOUT_S = 30
RETRIES = 2

SYSTEM = """You convert a network description into JSON for a deterministic design engine.
Rules:
- Output ONE JSON object that matches this JSON schema: {schema}
- Copy only facts stated in the text. Do NOT choose cables, protocols, VLAN IDs or addresses beyond what is stated.
- If a required number (distance, host count) is not stated, leave that item out; never guess it.
- If no root_prefix is stated use "10.0.0.0/16".
- Use VLAN ids 10, 20, 30, ... for segments in the order they appear.
- No comments, no markdown, JSON only."""


class OpenRouterError(Exception):
    pass


def configured() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY", "").strip())


def complete(text: str, client: httpx.Client | None = None) -> dict:
    """Return the parsed JSON object from the model. Raises OpenRouterError on transport/format errors."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set")
    body = {
        "model": os.environ.get("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM.format(schema=json.dumps(DesignInput.model_json_schema()))},
            {"role": "user", "content": text},
        ],
    }
    headers = {"Authorization": f"Bearer {key}", "X-Title": "NetArchitect"}
    own = client is None
    client = client or httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_S)
    try:
        last: Exception | None = None
        for _ in range(RETRIES + 1):
            try:
                r = client.post("/chat/completions", json=body, headers=headers)
            except httpx.HTTPError as e:
                last = e
                continue
            if r.status_code >= 500 or r.status_code == 429:
                last = OpenRouterError(f"OpenRouter HTTP {r.status_code}")
                continue
            if r.status_code != 200:
                raise OpenRouterError(f"OpenRouter HTTP {r.status_code}: {r.text[:200]}")
            content = r.json()["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise OpenRouterError(f"model did not return JSON: {e}") from None
        raise OpenRouterError(f"OpenRouter unreachable after {RETRIES + 1} attempts: {last}")
    finally:
        if own:
            client.close()
