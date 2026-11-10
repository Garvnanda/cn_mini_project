"""Phase 21: natural language -> design input. Result must be confirmed by the user before design runs."""

import httpx
from pydantic import BaseModel

from engine.errors import NetArchError
from engine.models import parse_design_input
from nl import fallback, openrouter


class NLResult(BaseModel):
    source: str              # openrouter | fallback
    input: dict              # extracted (possibly incomplete) design input
    valid: bool              # passes DesignInput validation as-is
    errors: list[dict] = []  # field errors when not valid
    assumptions: list[str] = []
    missing: list[str] = []
    note: str = ""


def extract(text: str, client: httpx.Client | None = None) -> NLResult:
    note = ""
    if openrouter.configured():
        try:
            data = openrouter.complete(text, client)
            return _check(NLResult(source="openrouter", input=data, valid=False,
                                   note="LLM extraction; confirm every value before designing"))
        except openrouter.OpenRouterError as e:
            note = f"OpenRouter failed ({e}); used offline parser"
    else:
        note = "OPENROUTER_API_KEY not set; used offline parser"
    data, assumptions, missing = fallback.parse(text)
    return _check(NLResult(source="fallback", input=data, valid=False, assumptions=assumptions,
                           missing=missing, note=note))


def _check(res: NLResult) -> NLResult:
    try:
        parse_design_input(res.input)
        res.valid = True
    except NetArchError as e:
        res.errors = e.details.get("errors", [{"loc": "", "msg": e.message}])
    return res
