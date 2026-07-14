"""Ethical disclaimer banner for ai-origin-trace.

This module exists to make one fact impossible to miss: ai-origin-trace does
not detect AI-generated text or code. It surfaces weak, explainable
stylometric SIGNALS -- discussion-starting data points for a human reviewer,
never a verdict. See README.md "Limitations & Responsible Use" for the long
version.
"""

_EQ_LINE = "=" * 78
_DASH_LINE = "-" * 78

BANNER_SHORT = "\n".join(
    [
        _EQ_LINE,
        " ai-origin-trace -- SIGNAL, NOT PROOF",
        _DASH_LINE,
        " This is a transparent, offline STYLOMETRIC SIGNAL, not an AI detector.",
        " It is NOT proof of AI authorship, NOT admissible as sole evidence in any",
        " academic-integrity / employment / legal process, and NOT a replacement",
        " for due process or a direct conversation with the author. Stylometric",
        " heuristics have HIGH false-positive and false-negative rates.",
        " Run with --disclaimer for the full statement. Suppress this banner",
        " (not recommended) with --quiet-banner.",
        _EQ_LINE,
    ]
)

BANNER_FULL = "\n".join(
    [
        _EQ_LINE,
        " ai-origin-trace -- ETHICAL USE DISCLAIMER",
        _EQ_LINE,
        "",
        "WHAT THIS TOOL IS:",
        "  A fully offline, fully transparent set of stylometric heuristics that",
        "  estimate surface-level writing/coding patterns often associated (weakly",
        "  and inconsistently) with either AI-generated or human-authored text.",
        "  Every score is explained feature-by-feature. There is no hidden model,",
        "  no black-box classifier, and no network call to a third-party",
        "  detection API.",
        "",
        "WHAT THIS TOOL IS NOT:",
        "  - It is NOT proof that a document was or was not written by an AI.",
        "  - It is NOT a replacement for due process, academic-integrity",
        "    procedures, or a direct conversation with the author.",
        "  - It should NEVER be used as the SOLE piece of evidence in any",
        "    accusation, grade dispute, hiring decision, or legal matter.",
        "  - It does NOT output a confidence percentage such as '87% AI-generated'",
        "    -- that phrasing implies a false precision that stylometry cannot",
        "    support, and this tool refuses to produce it.",
        "",
        "WHY THIS MATTERS:",
        "  Commercial 'AI detectors' have produced real, documented harm: false",
        "  academic-integrity accusations against students (including",
        "  disproportionate impact on non-native English speakers), wrongful",
        "  disciplinary action, and reputational damage, often from an opaque",
        "  single score that reviewers over-trusted. ai-origin-trace exists to",
        "  demonstrate a more honest alternative: show the reviewer exactly what",
        "  was measured, why, and how weak each signal is on its own -- and",
        "  actively resist being used as an accusation machine.",
        "",
        "RESPONSIBLE USE:",
        "  - Treat every result as a conversation-starter, not a conclusion.",
        "  - Corroborate with the author directly before taking any action.",
        "  - Never cite a single feature or the overall lean as 'proof'.",
        "  - Expect both false positives (human text flagged AI-like) and false",
        "    negatives (AI text flagged human-like); this is inherent to",
        "    stylometry, not a bug to be tuned away.",
        _EQ_LINE,
    ]
)


def print_banner(full: bool = False) -> None:
    """Print the disclaimer banner. Called on every CLI invocation by default."""
    print(BANNER_FULL if full else BANNER_SHORT)
