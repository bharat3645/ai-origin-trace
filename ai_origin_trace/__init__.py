"""ai-origin-trace: a transparent, offline stylometric AI-vs-human authorship SIGNAL estimator.

IMPORTANT ETHICAL NOTE (read before using this package):
This library produces a per-feature, fully explainable stylometric SIGNAL about
text or code -- it does NOT produce, and must never be represented as, proof of
AI authorship. Every heuristic here is a weak, contestable signal drawn from
surface statistics (sentence-length variance, function-word ratios, n-gram
repetition, vocabulary richness for text; comment density, naming entropy,
docstring boilerplate, and style consistency for code). Any of these can be
triggered by ordinary human writing/coding habits, translated prose, technical
writing conventions, terse styles, or deliberate editing.

Do not use this tool as sole evidence in an academic-integrity, employment, or
legal proceeding. Always corroborate with a direct conversation with the
author. See DISCLAIMER in ai_origin_trace.disclaimer for the full text, which
is also printed by the CLI on every invocation.
"""

__version__ = "0.1.0"
