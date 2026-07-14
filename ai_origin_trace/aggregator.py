"""Aggregation layer: combines per-feature signals into a single, clearly
labeled, non-numeric-precision "overall lean" -- deliberately NOT a single
opaque score, and deliberately NEVER phrased as a percentage or as
"X% AI-generated". That phrasing implies a false precision that stylometry
cannot support and is explicitly banned from this tool's output.

The per-feature breakdown (raw value + direction + plain-English
explanation) is always the primary output; the overall label is a coarse
summary of that breakdown, not a replacement for reading it.
"""

from __future__ import annotations

from collections import Counter
from typing import List

DIRECTION_WEIGHTS = {"ai-like": 1, "human-like": -1, "neutral": 0, "inconclusive": 0}

STRENGTH_INCONCLUSIVE = 0.15
STRENGTH_WEAK = 0.35
STRENGTH_MODERATE = 0.60


def compute_overall_signal(directions: List[str]) -> str:
    """Turn a list of per-feature directions into one coarse, labeled summary.

    This never emits a percentage or a single confident score. It emits one
    of:
      "Overall signal: inconclusive (no features were computed)"
      "Overall signal: inconclusive (no directional features available)"
      "Overall signal: inconclusive"
      "Overall signal: weak lean toward ai-like patterns"
      "Overall signal: moderate lean toward human-like patterns"
      "Overall signal: strong lean toward ai-like patterns"
    """
    if not directions:
        return "Overall signal: inconclusive (no features were computed)"

    counts = Counter(directions)
    ai_votes = counts.get("ai-like", 0)
    human_votes = counts.get("human-like", 0)
    decisive = ai_votes + human_votes

    if decisive == 0:
        return "Overall signal: inconclusive (no directional features available)"

    total = len(directions)
    net = (ai_votes - human_votes) / total
    magnitude = abs(net)

    if magnitude < STRENGTH_INCONCLUSIVE:
        return "Overall signal: inconclusive"

    if magnitude < STRENGTH_WEAK:
        strength = "weak"
    elif magnitude < STRENGTH_MODERATE:
        strength = "moderate"
    else:
        strength = "strong"

    lean = "ai-like" if net > 0 else "human-like"
    return "Overall signal: %s lean toward %s patterns" % (strength, lean)


def build_report(features: List[dict], mode: str) -> dict:
    """Assemble the full, non-collapsed report: per-feature breakdown + overall label."""
    directions = [f["direction"] for f in features]
    return {
        "mode": mode,
        "features": features,
        "overall_signal": compute_overall_signal(directions),
    }


def format_report_text(report: dict) -> str:
    """Render a report dict as a human-readable breakdown table + overall line."""
    lines = []
    lines.append("Mode: %s" % report["mode"])
    lines.append("-" * 78)
    lines.append("%-28s %-10s %-12s %s" % ("FEATURE", "VALUE", "DIRECTION", "EXPLANATION"))
    lines.append("-" * 78)
    for f in report["features"]:
        value = "n/a" if f["value"] is None else str(f["value"])
        lines.append("%-28s %-10s %-12s %s" % (f["name"], value, f["direction"], f["explanation"]))
    lines.append("-" * 78)
    lines.append(report["overall_signal"])
    lines.append(
        "Reminder: this is a discussion-starting SIGNAL for a human reviewer, "
        "not proof of AI or human authorship. Do not use it as sole evidence."
    )
    return "\n".join(lines)
