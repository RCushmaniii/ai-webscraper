"""
Evidence gate for the AI messaging review (the "Content & Brand" tab).

Why (2026-10-20): the strategy analysis handed a prospect's own AI assistant
an easy target: six unlike pages with the identical 75/80/70 sub-scores,
suggestions to add a value proposition and a CTA that were already on the
page, heading rewrites in the wrong case, and not one quoted line to check
any of it against. The model (gpt-4o-mini, 600 tokens) only ever sees a
skeleton of the page, so its opinions were unfalsifiable by construction.

The small fix, chosen over a rebuild: the scores are no longer stored or
shown, and a page's notes survive only when the model quotes copy that is
really in the skeleton it was given. Everything else is dropped in Python,
not trusted to the prompt. What remains is an AI reading with its evidence
attached, labelled as such.
"""

import re
import unicodedata
from typing import Any, Dict, List, Tuple

SCORE_KEYS = ("alignment_score", "tone_match_score", "skim_score", "overall_strategy_score")
MIN_QUOTE_CHARS = 8

_WS = re.compile(r"\s+")
_QUOTES = re.compile(r"[\"'‘’“”`]")
_ELLIPSIS = re.compile(r"(\.\.\.|…)")


def normalize(text: str) -> str:
    """Case-, quote-, dash- and whitespace-insensitive form for matching."""
    text = unicodedata.normalize("NFKC", text or "")
    text = _QUOTES.sub("", text)
    text = _ELLIPSIS.sub(" ", text)
    text = text.replace("—", "-").replace("–", "-")
    return _WS.sub(" ", text).strip().lower()


def skeleton_text(skeleton: Dict[str, Any]) -> str:
    """Everything the model was shown, as one searchable string."""
    parts: List[str] = [str(skeleton.get("title") or ""), str(skeleton.get("meta_description") or "")]
    headings = skeleton.get("headings") or {}
    parts += [str(h) for h in (headings.get("h1") or [])]
    parts += [str(h) for h in (headings.get("h2s") or [])]
    parts += [str(p) for p in (skeleton.get("paragraph_openers") or [])]
    parts += [str(c) for c in (skeleton.get("cta_buttons") or [])]
    return normalize(" \n ".join(parts))


def verify_quotes(quotes: List[str], skeleton: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Split quotes into (found in the skeleton, not found)."""
    haystack = skeleton_text(skeleton)
    verified: List[str] = []
    rejected: List[str] = []
    for raw in quotes or []:
        quote = str(raw or "").strip()
        needle = normalize(quote)
        if len(needle) >= MIN_QUOTE_CHARS and needle in haystack:
            verified.append(quote)
        else:
            rejected.append(quote)
    return verified, rejected


def gate_analysis(analysis: Dict[str, Any], skeleton: Dict[str, Any]) -> Dict[str, Any]:
    """The analysis as the report stores and shows it.

    - Scores are removed (they were never measurements).
    - ``evidence`` keeps only quotes that exist in the skeleton.
    - With no verified quote, every list of gaps/issues/suggestions and the
      top recommendation are emptied and ``evidence_verified`` is False, so
      the UI can say "no verifiable finding" instead of showing an opinion.
    """
    out: Dict[str, Any] = {}
    for key, value in (analysis or {}).items():
        if key in SCORE_KEYS:
            continue
        if isinstance(value, dict):
            out[key] = {k: v for k, v in value.items() if k not in SCORE_KEYS}
        else:
            out[key] = value

    verified, rejected = verify_quotes(list(analysis.get("evidence") or []), skeleton)
    out["evidence"] = verified
    out["evidence_rejected_count"] = len(rejected)
    out["evidence_verified"] = bool(verified)

    if not verified:
        out["top_recommendation"] = None
        for section, lists in (
            ("intent_gap", ("gaps", "suggestions")),
            ("tone_audit", ("issues",)),
            ("skim_test", ("missing_beats", "rewrite_suggestions")),
        ):
            block = out.get(section)
            if isinstance(block, dict):
                for name in lists:
                    if name in block:
                        block[name] = []
    return out
