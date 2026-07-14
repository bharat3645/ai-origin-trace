"""Tests for the math/logic of text-mode feature extractors.

These tests assert that each heuristic moves in the expected direction on
constructed fixtures with KNOWN characteristics (e.g. uniform vs. varied
sentence length). They do NOT and cannot assert "this text really is
AI-written" -- that ground-truth claim is exactly what this tool refuses to
make. See ai_origin_trace/disclaimer.py.
"""

import math

from ai_origin_trace.text_features import (
    burstiness,
    function_word_ratio,
    moving_average_ttr,
    repetition_score,
    split_sentences,
    tokenize_words,
    vocabulary_richness,
)

UNIFORM_SENTENCES = (
    "The cat sat on the mat today. The dog ran in the park today. "
    "The bird flew over the tree today. The fish swam in the pond today. "
    "The mouse hid under the box today. The frog jumped near the pond today."
)

VARIED_SENTENCES = (
    "Rain. The old harbor smelled of diesel and salt, and nobody spoke for a "
    "long while after the boat finally came in. Why? Because grief has its "
    "own tide tables, and none of us had memorized them yet, not even the "
    "captain, who usually knew everything about timing and almost nothing "
    "about people."
)


def test_split_sentences_basic():
    sentences = split_sentences("Hello world. How are you? I am fine!")
    assert len(sentences) == 3


def test_tokenize_words_basic():
    words = tokenize_words("Hello, World! Don't stop.")
    assert words == ["hello", "world", "don't", "stop"]


def test_burstiness_uniform_is_ai_like():
    result = burstiness(UNIFORM_SENTENCES)
    assert result["direction"] == "ai-like"
    assert result["value"] is not None
    assert result["value"] < 0.35


def test_burstiness_varied_is_human_like():
    result = burstiness(VARIED_SENTENCES)
    assert result["direction"] == "human-like"
    assert result["value"] > 0.55


def test_burstiness_inconclusive_on_short_input():
    result = burstiness("One sentence only.")
    assert result["direction"] == "inconclusive"
    assert result["value"] is None


def test_function_word_ratio_high_is_ai_like():
    text = (
        "This is the of and to the of and to the of and to the of and to "
        "the of and to the of and to the of and to the of and to the of."
    )
    result = function_word_ratio(text)
    assert result["value"] > 0.60
    assert result["direction"] == "ai-like"


def test_function_word_ratio_low_is_human_like():
    text = (
        "Photosynthesis converts sunlight carbon dioxide water glucose oxygen "
        "chlorophyll thylakoid stroma mitochondria ribosome nucleotide enzyme "
        "catalysis metabolism biosynthesis chromosome polymerase transcription"
    )
    result = function_word_ratio(text)
    assert result["value"] < 0.40
    assert result["direction"] == "human-like"


def test_repetition_score_high_on_repeated_phrases():
    text = (
        "we must move forward together. we must move forward together. "
        "we must move forward together. we must move forward together. "
        "we must move forward together as one unified team of dedicated "
        "professionals working toward a common goal each and every day."
    )
    result = repetition_score(text, n=4)
    assert result["direction"] == "ai-like"
    assert result["value"] > 0.15


def test_repetition_score_low_on_varied_text():
    result = repetition_score(VARIED_SENTENCES, n=4)
    assert result["direction"] in ("human-like", "neutral")
    assert result["value"] < 0.15


def test_moving_average_ttr_hand_computed_example():
    # words: a b a b c, window=3
    # windows: [a,b,a]=2/3, [b,a,b]=2/3, [a,b,c]=3/3
    # mean = (2/3 + 2/3 + 3/3) / 3 = (0.6667+0.6667+1.0)/3 = 0.777778
    text = "a b a b c"
    result = moving_average_ttr(text, window=3)
    expected = (2 / 3 + 2 / 3 + 3 / 3) / 3
    assert math.isclose(result, expected, rel_tol=1e-9)
    assert math.isclose(result, 0.7777777777777778, rel_tol=1e-6)


def test_moving_average_ttr_short_text_uses_raw_ttr():
    # fewer words than window -> falls back to raw TTR.
    # words: a b a b c -> unique = {a, b, c} = 3, total = 5
    text = "a b a b c"
    result = moving_average_ttr(text, window=50)
    assert math.isclose(result, 3 / 5)


def test_vocabulary_richness_repetitive_is_ai_like_or_neutral():
    repetitive = " ".join(["same word repeated text"] * 20)
    result = vocabulary_richness(repetitive, window=10)
    assert result["value"] < 0.70


def test_vocabulary_richness_rich_is_human_like():
    rich_words = [
        "quixotic", "ephemeral", "labyrinthine", "susurrus", "petrichor",
        "penumbra", "vestige", "cacophony", "solstice", "mercurial",
        "obfuscate", "paradigm", "resilience", "serendipity", "wistful",
    ]
    text = " ".join(rich_words)
    result = vocabulary_richness(text, window=10)
    assert result["direction"] == "human-like"
    assert result["value"] > 0.70
