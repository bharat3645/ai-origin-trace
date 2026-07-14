"""Tests for the aggregator's direction-labeling logic.

These test the pure math of turning a list of per-feature directions into
one coarse overall-signal label. They do not (and must not) test any
ground-truth "is this AI" claim.
"""

from ai_origin_trace.aggregator import build_report, compute_overall_signal


def test_all_ai_like_is_strong_lean_ai():
    label = compute_overall_signal(["ai-like", "ai-like", "ai-like", "ai-like"])
    assert label == "Overall signal: strong lean toward ai-like patterns"


def test_all_human_like_is_strong_lean_human():
    label = compute_overall_signal(["human-like"] * 5)
    assert label == "Overall signal: strong lean toward human-like patterns"


def test_balanced_ai_and_human_is_inconclusive():
    label = compute_overall_signal(["ai-like", "human-like", "neutral", "inconclusive"])
    assert label == "Overall signal: inconclusive"


def test_all_neutral_or_inconclusive_has_no_directional_features():
    label = compute_overall_signal(["neutral", "neutral", "inconclusive"])
    assert label == "Overall signal: inconclusive (no directional features available)"


def test_empty_directions_list():
    label = compute_overall_signal([])
    assert label == "Overall signal: inconclusive (no features were computed)"


def test_moderate_lean_ai():
    # net = (2 - 0) / 4 = 0.5 -> moderate (0.35 <= 0.5 < 0.60)
    label = compute_overall_signal(["ai-like", "ai-like", "neutral", "neutral"])
    assert label == "Overall signal: moderate lean toward ai-like patterns"


def test_weak_lean_human():
    # net = (0 - 2) / 8 = -0.25 -> weak (0.15 <= 0.25 < 0.35)
    directions = ["human-like", "human-like"] + ["neutral"] * 6
    label = compute_overall_signal(directions)
    assert label == "Overall signal: weak lean toward human-like patterns"


def test_no_percentage_phrasing_anywhere_in_labels():
    # Hard requirement: never phrase output as "X% AI-generated".
    for directions in (
        ["ai-like"] * 4,
        ["human-like"] * 4,
        ["neutral"] * 4,
        [],
    ):
        label = compute_overall_signal(directions)
        assert "%" not in label
        assert "generated" not in label.lower()


def test_build_report_shape():
    features = [
        {"name": "f1", "value": 0.1, "direction": "ai-like", "explanation": "x"},
        {"name": "f2", "value": 0.9, "direction": "human-like", "explanation": "y"},
    ]
    report = build_report(features, mode="text")
    assert report["mode"] == "text"
    assert report["features"] == features
    assert report["overall_signal"] == "Overall signal: inconclusive"
