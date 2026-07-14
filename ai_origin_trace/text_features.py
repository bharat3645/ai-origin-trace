"""Text-mode stylometric feature extractors.

Every function in this module returns a *weak, contestable* signal about a
single surface statistic of the input text. None of these signals -- alone
or combined -- constitute proof of AI or human authorship. See
ai_origin_trace.disclaimer for the full ethical framing, which is printed by
the CLI on every run.

Design notes:
- Tokenization is a plain regex fallback by default. If ``nltk`` is
  installed *and* its ``punkt`` data is available, we opportunistically use
  it for slightly better sentence splitting -- but a missing nltk install or
  missing corpus download must never break this tool, so all nltk use is
  wrapped in a broad try/except that falls back to the regex tokenizer.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from typing import List, Optional

# ---------------------------------------------------------------------------
# Tokenization (regex fallback, optional nltk upgrade)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z']+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])|(?<=[.!?])\s*\n+")

_NLTK_SENT_TOKENIZER = None
_NLTK_CHECKED = False


def _try_load_nltk():
    """Attempt to load nltk's sentence tokenizer. Never raises."""
    global _NLTK_SENT_TOKENIZER, _NLTK_CHECKED
    if _NLTK_CHECKED:
        return _NLTK_SENT_TOKENIZER
    _NLTK_CHECKED = True
    try:
        import nltk  # type: ignore

        try:
            from nltk.tokenize import sent_tokenize  # type: ignore

            # Smoke-test: this will raise LookupError if the punkt data
            # isn't downloaded. We must not let that escape.
            sent_tokenize("Smoke test sentence. Second one.")
            _NLTK_SENT_TOKENIZER = sent_tokenize
        except Exception:
            _NLTK_SENT_TOKENIZER = None
    except Exception:
        _NLTK_SENT_TOKENIZER = None
    return _NLTK_SENT_TOKENIZER


def split_sentences(text: str) -> List[str]:
    """Split text into sentences. Tries nltk, always falls back to regex."""
    text = text.strip()
    if not text:
        return []
    tokenizer = _try_load_nltk()
    if tokenizer is not None:
        try:
            sentences = tokenizer(text)
            if sentences:
                return [s.strip() for s in sentences if s.strip()]
        except Exception:
            pass
    # Regex fallback: split on sentence-ending punctuation.
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def tokenize_words(text: str) -> List[str]:
    """Lowercase alphabetic word tokens, apostrophes kept (don't -> don't)."""
    return [w.lower() for w in _WORD_RE.findall(text)]


# ---------------------------------------------------------------------------
# Feature: burstiness
# ---------------------------------------------------------------------------

# Thresholds on the coefficient of variation (stdev / mean) of sentence
# length in words. Human writing tends to mix short punchy sentences with
# long ones (high CV); very uniform sentence length (low CV) is a weak
# signal of templated/generated text. These cutoffs are heuristic, documented
# choices, not empirically calibrated against a labeled corpus.
BURSTINESS_LOW = 0.35   # below this: suspiciously uniform -> ai-like
BURSTINESS_HIGH = 0.55  # above this: clearly varied -> human-like


def burstiness(text: str) -> dict:
    """Coefficient of variation of sentence length (in words).

    burstiness = stdev(sentence_lengths) / mean(sentence_lengths)

    Low burstiness (very uniform sentence lengths) is a weak AI-like signal;
    high burstiness (mixed short/long sentences) is a weak human-like signal.
    """
    sentences = split_sentences(text)
    lengths = [len(tokenize_words(s)) for s in sentences]
    lengths = [l for l in lengths if l > 0]

    if len(lengths) < 3:
        return {
            "name": "burstiness",
            "value": None,
            "direction": "inconclusive",
            "explanation": (
                "Too few sentences (%d) to measure sentence-length variance "
                "reliably; need at least 3." % len(lengths)
            ),
        }

    mean = statistics.mean(lengths)
    stdev = statistics.pstdev(lengths)
    cv = (stdev / mean) if mean > 0 else 0.0

    if cv < BURSTINESS_LOW:
        direction = "ai-like"
        explanation = (
            "Sentence lengths are very uniform (CV=%.2f, below %.2f); "
            "generated text often has less natural rhythm variation." % (cv, BURSTINESS_LOW)
        )
    elif cv > BURSTINESS_HIGH:
        direction = "human-like"
        explanation = (
            "Sentence lengths vary a lot (CV=%.2f, above %.2f); human writing "
            "commonly mixes short and long sentences." % (cv, BURSTINESS_HIGH)
        )
    else:
        direction = "neutral"
        explanation = (
            "Sentence-length variation (CV=%.2f) is in a middling range that "
            "doesn't lean strongly either way." % cv
        )

    return {"name": "burstiness", "value": round(cv, 4), "direction": direction, "explanation": explanation}


# ---------------------------------------------------------------------------
# Feature: function-word ratio
# ---------------------------------------------------------------------------

# A small, fixed list of common English function words (articles,
# prepositions, conjunctions, common pronouns/auxiliaries). This is not
# exhaustive; it is a documented, fixed baseline list chosen for stability
# and reproducibility rather than corpus-derived tuning.
FUNCTION_WORDS = frozenset(
    """
    the of and a to in is that it for on with as was be at by an this
    which or from have has had not but they you he she we i are were
    been being do does did will would shall should can could may might
    must there here what when where who whom whose why how all any
    each few more most other some such no nor so than too very just
    if then because while about above after before between into through
    during without within over under again further once
    """.split()
)

# Documented "typical human baseline" range for function-word ratio in
# general English prose, drawn from standard corpus-linguistics observations
# that function words make up roughly 40-60% of running text. Text outside
# this band isn't wrong, just atypical for the baseline this tool assumes.
FUNCTION_WORD_BASELINE_LOW = 0.40
FUNCTION_WORD_BASELINE_HIGH = 0.60


def function_word_ratio(text: str) -> dict:
    """Ratio of function words to total word tokens.

    Compared against a fixed documented baseline of 0.40-0.60 for typical
    English prose. A ratio noticeably above baseline is a weak AI-like signal
    (simple connective-heavy phrasing is common in generated text); a ratio
    noticeably below baseline is a weak human-like signal (denser,
    idiosyncratic or technical vocabulary).
    """
    words = tokenize_words(text)
    if len(words) < 10:
        return {
            "name": "function_word_ratio",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Too few words (%d) to measure function-word ratio reliably." % len(words),
        }

    fw_count = sum(1 for w in words if w in FUNCTION_WORDS)
    ratio = fw_count / len(words)

    if ratio > FUNCTION_WORD_BASELINE_HIGH:
        direction = "ai-like"
        explanation = (
            "Function-word ratio (%.2f) is above the typical human baseline "
            "(%.2f-%.2f); heavy reliance on connective words can indicate "
            "simplified/templated phrasing." % (ratio, FUNCTION_WORD_BASELINE_LOW, FUNCTION_WORD_BASELINE_HIGH)
        )
    elif ratio < FUNCTION_WORD_BASELINE_LOW:
        direction = "human-like"
        explanation = (
            "Function-word ratio (%.2f) is below the typical human baseline "
            "(%.2f-%.2f); denser, idiosyncratic vocabulary is more common in "
            "human writing." % (ratio, FUNCTION_WORD_BASELINE_LOW, FUNCTION_WORD_BASELINE_HIGH)
        )
    else:
        direction = "neutral"
        explanation = (
            "Function-word ratio (%.2f) falls within the typical human "
            "baseline (%.2f-%.2f)." % (ratio, FUNCTION_WORD_BASELINE_LOW, FUNCTION_WORD_BASELINE_HIGH)
        )

    return {"name": "function_word_ratio", "value": round(ratio, 4), "direction": direction, "explanation": explanation}


# ---------------------------------------------------------------------------
# Feature: repetition / template score (n-gram repetition rate)
# ---------------------------------------------------------------------------

REPETITION_HIGH = 0.15  # above this fraction of repeated n-grams -> ai-like
REPETITION_LOW = 0.03   # below this -> human-like


def repetition_score(text: str, n: int = 4) -> dict:
    """Fraction of n-grams (default 4-grams) that occur more than once.

    A high repetition rate is a weak AI-like signal (templated / formulaic
    phrasing); a low rate is a weak human-like signal.
    """
    words = tokenize_words(text)
    if len(words) < n + 5:
        return {
            "name": "repetition_score",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Too few words (%d) to compute reliable %d-gram repetition." % (len(words), n),
        }

    grams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
    total = len(grams)
    counts = Counter(grams)
    repeated = sum(c for c in counts.values() if c > 1)
    rate = repeated / total if total else 0.0

    if rate > REPETITION_HIGH:
        direction = "ai-like"
        explanation = (
            "%.1f%% of %d-grams repeat verbatim elsewhere in the text; "
            "high phrase repetition can indicate templated phrasing." % (rate * 100, n)
        )
    elif rate < REPETITION_LOW:
        direction = "human-like"
        explanation = (
            "Only %.1f%% of %d-grams repeat; low phrase repetition is typical "
            "of freely composed human writing." % (rate * 100, n)
        )
    else:
        direction = "neutral"
        explanation = "%.1f%% of %d-grams repeat, a middling amount." % (rate * 100, n)

    return {"name": "repetition_score", "value": round(rate, 4), "direction": direction, "explanation": explanation}


# ---------------------------------------------------------------------------
# Feature: vocabulary richness (MATTR -- Moving Average Type-Token Ratio)
# ---------------------------------------------------------------------------

MATTR_WINDOW_DEFAULT = 50
MATTR_HIGH = 0.70  # above this -> human-like (richer local vocabulary)
MATTR_LOW = 0.50   # below this -> ai-like (repetitive local vocabulary)


def moving_average_ttr(text: str, window: int = MATTR_WINDOW_DEFAULT) -> Optional[float]:
    """Moving Average Type-Token Ratio.

    Raw type-token ratio (unique words / total words) shrinks mechanically
    as text gets longer, which makes it useless for comparing texts of
    different lengths. MATTR fixes this by sliding a fixed-size window
    across the token stream, computing TTR within each window, and
    averaging -- so the result stays comparable regardless of overall text
    length (Covington & McFall, 2010).

    Returns None if there are no words at all.
    """
    words = tokenize_words(text)
    n = len(words)
    if n == 0:
        return None
    if n <= window:
        return len(set(words)) / n

    ratios = []
    for i in range(0, n - window + 1):
        w = words[i : i + window]
        ratios.append(len(set(w)) / window)
    return statistics.mean(ratios)


def vocabulary_richness(text: str, window: int = MATTR_WINDOW_DEFAULT) -> dict:
    """Vocabulary richness feature wrapper around moving_average_ttr()."""
    words = tokenize_words(text)
    if len(words) < 10:
        return {
            "name": "vocabulary_richness",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Too few words (%d) to measure vocabulary richness reliably." % len(words),
        }

    mattr = moving_average_ttr(text, window=window)
    effective_window = min(window, len(words))

    if mattr is None:
        return {
            "name": "vocabulary_richness",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Could not compute MATTR (empty token stream).",
        }

    if mattr > MATTR_HIGH:
        direction = "human-like"
        explanation = (
            "Moving-window vocabulary richness (MATTR=%.2f, window=%d) is high; "
            "varied local word choice is more typical of human writing." % (mattr, effective_window)
        )
    elif mattr < MATTR_LOW:
        direction = "ai-like"
        explanation = (
            "Moving-window vocabulary richness (MATTR=%.2f, window=%d) is low; "
            "repetitive local word choice can indicate generated text, though "
            "some LLM output is also lexically rich, so this signal is weak." % (mattr, effective_window)
        )
    else:
        direction = "neutral"
        explanation = "Moving-window vocabulary richness (MATTR=%.2f) is in a middling range." % mattr

    return {
        "name": "vocabulary_richness",
        "value": round(mattr, 4),
        "direction": direction,
        "explanation": explanation,
    }


def extract_text_features(text: str) -> List[dict]:
    """Run every text-mode feature extractor and return the list of results."""
    return [
        burstiness(text),
        function_word_ratio(text),
        repetition_score(text),
        vocabulary_richness(text),
    ]
