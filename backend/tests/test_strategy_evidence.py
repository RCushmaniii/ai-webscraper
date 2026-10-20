"""The messaging review keeps a note only when it quotes copy that exists."""

from app.services.strategy_evidence import gate_analysis, normalize, skeleton_text, verify_quotes
from app.services.semantic_builder import infer_page_purpose

SKELETON = {
    "url": "https://www.cushlabs.ai/pricing/",
    "title": "Pricing | CushLabs",
    "meta_description": "From $129 USD/mo ($1,990 MXN in Mexico). No setup fee, no contract.",
    "inferred_purpose": "pricing",
    "headings": {"h1": ["Simple, transparent pricing"], "h2s": ["Not sure which plan fits?"]},
    "paragraph_openers": ["One monthly price. Everything set up and managed for you."],
    "cta_buttons": ["Book a Free 30-Min Call"],
}

ANALYSIS = {
    "intent_gap": {"alignment_score": 70, "assessment": "ok", "gaps": ["g"], "suggestions": ["s"]},
    "tone_audit": {"tone_match_score": 75, "detected_tone": "balanced", "audience_fit": "fits", "issues": ["i"]},
    "skim_test": {"skim_score": 65, "story_assessment": "meh", "missing_beats": ["b"], "rewrite_suggestions": ["r"]},
    "overall_strategy_score": 70,
    "top_recommendation": "Add proof near the plan cards.",
    "suggested_title": None,
    "suggested_meta": None,
    "evidence": [],
}


def test_normalize_ignores_case_quotes_and_dashes():
    assert normalize('  "Simple,  transparent — pricing" ') == "simple, transparent - pricing"


def test_skeleton_text_contains_every_field_shown_to_the_model():
    text = skeleton_text(SKELETON)
    for needle in ("pricing | cushlabs", "no setup fee", "simple, transparent pricing", "one monthly price", "book a free 30-min call"):
        assert needle in text


def test_verify_quotes_splits_real_from_invented():
    verified, rejected = verify_quotes(
        ['"Book a Free 30-Min Call"', "Not sure which plan fits?", "Unlock Simple Pricing for AI Solutions", "ok"],
        SKELETON,
    )
    assert verified == ['"Book a Free 30-Min Call"', "Not sure which plan fits?"]
    assert rejected == ["Unlock Simple Pricing for AI Solutions", "ok"]


def test_gate_drops_scores_and_keeps_notes_with_evidence():
    out = gate_analysis({**ANALYSIS, "evidence": ["Simple, transparent pricing", "made up line"]}, SKELETON)
    assert "overall_strategy_score" not in out
    assert "alignment_score" not in out["intent_gap"]
    assert out["evidence"] == ["Simple, transparent pricing"]
    assert out["evidence_rejected_count"] == 1
    assert out["evidence_verified"] is True
    assert out["top_recommendation"] == "Add proof near the plan cards."
    assert out["intent_gap"]["gaps"] == ["g"]


def test_gate_empties_notes_without_evidence():
    out = gate_analysis(ANALYSIS, SKELETON)
    assert out["evidence_verified"] is False
    assert out["top_recommendation"] is None
    assert out["intent_gap"]["gaps"] == [] and out["intent_gap"]["suggestions"] == []
    assert out["tone_audit"]["issues"] == []
    assert out["skim_test"]["missing_beats"] == [] and out["skim_test"]["rewrite_suggestions"] == []
    # Descriptive prose stays; it is labelled as an AI reading in the UI.
    assert out["tone_audit"]["detected_tone"] == "balanced"


def test_pricing_is_its_own_purpose():
    assert infer_page_purpose("https://www.cushlabs.ai/pricing/") == "pricing"
    assert infer_page_purpose("https://x.example/plans") == "pricing"
    assert infer_page_purpose("https://x.example/contact") == "lead_generation"


def test_cta_extractor_ignores_site_chrome():
    from bs4 import BeautifulSoup
    from app.services.semantic_builder import extract_cta_buttons

    html = """
    <button aria-label="Toggle theme">Toggle theme</button>
    <button class="menu-btn" aria-expanded="false">Menu</button>
    <button>Accept cookies</button>
    <button>Book a Free 30-Min Call</button>
    <a class="btn-primary" href="/trial">Start Your Free Trial</a>
    <button>Next</button>
    """
    assert extract_cta_buttons(BeautifulSoup(html, "html.parser")) == ["Book a Free 30-Min Call", "Start Your Free Trial"]
