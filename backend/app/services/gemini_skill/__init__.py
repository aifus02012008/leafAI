"""Gemini leaf skill: diagnose a leaf photo with Gemini Vision, constrained to LEAF_AI's disease library.

Used for crops without a trained model (mangosteen, rambutan) and as a fallback when a crop model
is unsure. Output is always validated against a fixed schema and the crop's known disease names,
so it plugs into the same treatment plan / actives / chat flow as model results.
"""
from app.services.gemini_skill.schema import GeminiLeafVerdict, parse_verdict, response_schema
from app.services.gemini_skill.service import (
    GeminiSkillError,
    GeminiSkillRateLimited,
    diagnose_leaf,
    is_enabled,
    reset_cache,
)

__all__ = [
    "GeminiLeafVerdict",
    "GeminiSkillError",
    "GeminiSkillRateLimited",
    "diagnose_leaf",
    "is_enabled",
    "parse_verdict",
    "reset_cache",
    "response_schema",
]
