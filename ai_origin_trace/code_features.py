"""Code-mode stylometric feature extractors.

Operates on raw source-file text using simple, language-agnostic regex
heuristics (comment markers, quote characters, indentation, docstring
scaffolding). A couple of checks lean Python-flavored (triple-quoted
docstrings, snake_case/camelCase identifier buckets) but degrade gracefully
on other C-like languages since they only look for generic textual patterns.

As with text_features.py: every score here is a weak, contestable signal,
never proof of AI or human authorship. See ai_origin_trace.disclaimer.
"""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from typing import List

_COMMENT_PREFIXES = ("#", "//", "/*", "*", "--")

_DOCSTRING_RE = re.compile(r'("""|\'\'\')(.*?)\1', re.DOTALL)
_SCAFFOLD_KEYWORDS = [
    "Args:",
    "Arguments:",
    "Parameters:",
    "Returns:",
    "Return:",
    "Raises:",
    "Yields:",
    "Example:",
    "Examples:",
    "Note:",
    "Attributes:",
]

_ASSIGN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)")
_SINGLE_QUOTED_RE = re.compile(r"'[^'\n\\]*(?:\\.[^'\n\\]*)*'")
_DOUBLE_QUOTED_RE = re.compile(r'"[^"\n\\]*(?:\\.[^"\n\\]*)*"')
# Bare '=' not part of ==, !=, <=, >=, +=, -=, *=, /=, %=, ^=, &=, |=
_BARE_EQUALS_RE = re.compile(r"(?<![=!<>+\-*/%^&|])=(?!=)")


# ---------------------------------------------------------------------------
# Feature: comment density + its consistency across the file
# ---------------------------------------------------------------------------


def _is_comment_line(line: str) -> bool:
    s = line.strip()
    return s.startswith(_COMMENT_PREFIXES)


def comment_density(code: str) -> dict:
    """Fraction of non-blank lines that are comment lines.

    Reported for context; on its own this raw ratio has no fixed
    "correct" baseline (comment density varies hugely by language, house
    style, and file type), so this feature is informational (direction
    always 'neutral'). See comment_density_consistency() for the
    signal-bearing measurement -- suspiciously *uniform* comment density
    across a file is the actual weak AI-like signal.
    """
    lines = code.splitlines()
    non_blank = [l for l in lines if l.strip()]
    if len(non_blank) < 5:
        return {
            "name": "comment_density",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Too few non-blank lines (%d) to measure comment density." % len(non_blank),
        }

    comment_lines = sum(1 for l in non_blank if _is_comment_line(l))
    density = comment_lines / len(non_blank)
    return {
        "name": "comment_density",
        "value": round(density, 4),
        "direction": "neutral",
        "explanation": (
            "%.1f%% of non-blank lines are comments. Reported for context; the "
            "consistency of this ratio across the file (see "
            "comment_density_consistency) is the actual weak signal." % (density * 100)
        ),
    }


COMMENT_CONSISTENCY_LOW_STDEV = 0.04   # very uniform across chunks -> ai-like
COMMENT_CONSISTENCY_HIGH_STDEV = 0.12  # clearly uneven across chunks -> human-like


def comment_density_consistency(code: str, chunks: int = 4) -> dict:
    """Standard deviation of comment density across N equal chunks of the file.

    LLM-authored code often comments at a suspiciously constant rate line
    after line and function after function; human code tends to comment in
    bursts (heavy near tricky logic, sparse elsewhere). Low stdev across
    chunks is a weak AI-like signal; high stdev is a weak human-like signal.
    """
    lines = code.splitlines()
    non_blank = [l for l in lines if l.strip()]
    if len(non_blank) < chunks * 3:
        return {
            "name": "comment_density_consistency",
            "value": None,
            "direction": "inconclusive",
            "explanation": "File too short (%d non-blank lines) to split into %d chunks reliably." % (len(non_blank), chunks),
        }

    chunk_size = len(non_blank) // chunks
    densities = []
    for i in range(chunks):
        start = i * chunk_size
        end = start + chunk_size if i < chunks - 1 else len(non_blank)
        chunk = non_blank[start:end]
        if not chunk:
            continue
        c = sum(1 for l in chunk if _is_comment_line(l))
        densities.append(c / len(chunk))

    stdev = statistics.pstdev(densities) if len(densities) > 1 else 0.0

    if stdev < COMMENT_CONSISTENCY_LOW_STDEV:
        direction = "ai-like"
        explanation = (
            "Comment density is nearly identical across all %d sections of the "
            "file (stdev=%.3f); suspiciously uniform commenting rhythm can "
            "indicate generated code." % (chunks, stdev)
        )
    elif stdev > COMMENT_CONSISTENCY_HIGH_STDEV:
        direction = "human-like"
        explanation = (
            "Comment density varies noticeably across the file (stdev=%.3f); "
            "uneven commenting bursts are typical of human code." % stdev
        )
    else:
        direction = "neutral"
        explanation = "Comment density variation across the file (stdev=%.3f) is middling." % stdev

    return {
        "name": "comment_density_consistency",
        "value": round(stdev, 4),
        "direction": direction,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Feature: variable-naming entropy
# ---------------------------------------------------------------------------

_SNAKE_RE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)+$")
_CAMEL_RE = re.compile(r"^[a-z]+([A-Z][a-z0-9]*)+$")


def _classify_identifier(name: str) -> str:
    if len(name) == 1:
        return "single_letter"
    if name.isupper():
        return "all_caps"
    if _SNAKE_RE.match(name):
        return "snake_case"
    if _CAMEL_RE.match(name):
        return "camel_case"
    return "other"


NAMING_ENTROPY_LOW = 0.35   # normalized entropy below this -> ai-like (uniform style)
NAMING_ENTROPY_HIGH = 0.65  # above this -> human-like (mixed styles)


def variable_naming_entropy(code: str) -> dict:
    """Shannon entropy of variable-naming-convention buckets, normalized to [0, 1].

    Identifiers are bucketed into single_letter / snake_case / camel_case /
    all_caps / other, and we compute normalized Shannon entropy over that
    bucket distribution. Humans routinely mix naming conventions within one
    file (i, tmp, user_name, userName); very low entropy (one convention
    used everywhere) is a weak AI-like signal.
    """
    identifiers = _ASSIGN_RE.findall(code)
    if len(identifiers) < 5:
        return {
            "name": "variable_naming_entropy",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Too few assigned identifiers (%d) to measure naming entropy reliably." % len(identifiers),
        }

    buckets = Counter(_classify_identifier(name) for name in identifiers)
    total = sum(buckets.values())
    probs = [c / total for c in buckets.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)

    num_buckets_used = len(buckets)
    max_entropy = math.log2(num_buckets_used) if num_buckets_used > 1 else 1.0
    normalized = entropy / max_entropy if max_entropy > 0 else 0.0

    if normalized < NAMING_ENTROPY_LOW:
        direction = "ai-like"
        explanation = (
            "Variable names overwhelmingly follow a single naming convention "
            "(normalized entropy=%.2f); very uniform style can indicate "
            "generated code." % normalized
        )
    elif normalized > NAMING_ENTROPY_HIGH:
        direction = "human-like"
        explanation = (
            "Variable names mix multiple naming conventions (normalized "
            "entropy=%.2f); this messiness is typical of human code." % normalized
        )
    else:
        direction = "neutral"
        explanation = "Naming-convention entropy (%.2f) is middling." % normalized

    return {
        "name": "variable_naming_entropy",
        "value": round(normalized, 4),
        "direction": direction,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Feature: boilerplate docstring detection
# ---------------------------------------------------------------------------

BOILERPLATE_HIGH = 0.7  # fraction sharing the same scaffold signature -> ai-like
BOILERPLATE_LOW = 0.35


def _docstring_signature(body: str):
    lines = [l.strip() for l in body.splitlines()]
    return tuple(kw for kw in _SCAFFOLD_KEYWORDS if any(l.startswith(kw) for l in lines))


def boilerplate_docstring_score(code: str) -> dict:
    """Fraction of "scaffolded" docstrings that share an identical template signature.

    We only look at docstrings that contain at least one structural keyword
    (Args:, Returns:, Raises:, ...). Among those, if most of them reuse the
    exact same keyword scaffold (order and set), that's a weak AI-like
    signal -- LLMs tend to stamp out the same docstring skeleton for every
    function, while humans are inconsistent about which sections they
    bother to include.
    """
    docstrings = [body for _, body in _DOCSTRING_RE.findall(code)]
    scaffolded = [_docstring_signature(d) for d in docstrings]
    scaffolded = [sig for sig in scaffolded if sig]

    if len(scaffolded) < 3:
        return {
            "name": "boilerplate_docstring_score",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Fewer than 3 structured docstrings found (%d); not enough to compare templates." % len(scaffolded),
        }

    counts = Counter(scaffolded)
    most_common_sig, most_common_count = counts.most_common(1)[0]
    score = most_common_count / len(scaffolded)

    if score > BOILERPLATE_HIGH:
        direction = "ai-like"
        explanation = (
            "%.0f%% of structured docstrings (%d/%d) share the exact same "
            "section template %s; heavy scaffold reuse is a weak AI-like "
            "signal." % (score * 100, most_common_count, len(scaffolded), most_common_sig)
        )
    elif score < BOILERPLATE_LOW:
        direction = "human-like"
        explanation = (
            "Structured docstrings use varied templates (top template covers "
            "only %.0f%%); varied documentation style is typical of human "
            "code." % (score * 100)
        )
    else:
        direction = "neutral"
        explanation = "Docstring template reuse (%.0f%%) is middling." % (score * 100)

    return {
        "name": "boilerplate_docstring_score",
        "value": round(score, 4),
        "direction": direction,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Feature: style-consistency score (quotes, indentation, operator spacing)
# ---------------------------------------------------------------------------

STYLE_CONSISTENCY_HIGH = 0.95  # near-perfect uniformity -> ai-like
STYLE_CONSISTENCY_LOW = 0.75   # noticeably messy -> human-like


def _quote_consistency(code: str):
    singles = len(_SINGLE_QUOTED_RE.findall(code))
    doubles = len(_DOUBLE_QUOTED_RE.findall(code))
    total = singles + doubles
    if total < 4:
        return None
    return max(singles, doubles) / total


def _indent_consistency(code: str):
    indents = []
    for line in code.splitlines():
        if not line.strip():
            continue
        stripped = line.lstrip(" \t")
        leading = line[: len(line) - len(stripped)]
        if leading:
            indents.append(leading)
    if len(indents) < 4:
        return None
    tabs = sum(1 for i in indents if "\t" in i)
    spaces = sum(1 for i in indents if "\t" not in i)
    return max(tabs, spaces) / len(indents)


def _operator_spacing_consistency(code: str):
    spaced = len(re.findall(r"[^\s=!<>+\-*/%^&|]\s=\s[^=]", code))
    unspaced = len(re.findall(r"[^\s=!<>+\-*/%^&|]=[^\s=]", code))
    total = spaced + unspaced
    if total < 4:
        return None
    return max(spaced, unspaced) / total


def style_consistency_score(code: str) -> dict:
    """Average consistency of quote style, indentation, and operator spacing.

    Each sub-metric is "fraction following the majority convention" (1.0 =
    perfectly uniform). We average whichever sub-metrics have enough data
    to be meaningful. Extremely high uniformity (near 1.0 across the board)
    is a weak AI-like signal -- humans are reliably a little messier;
    noticeably lower uniformity is a weak human-like signal.
    """
    sub_scores = []
    for fn in (_quote_consistency, _indent_consistency, _operator_spacing_consistency):
        s = fn(code)
        if s is not None:
            sub_scores.append(s)

    if len(sub_scores) < 2:
        return {
            "name": "style_consistency_score",
            "value": None,
            "direction": "inconclusive",
            "explanation": "Not enough style data points (quotes/indentation/operator spacing) to score consistency.",
        }

    avg = statistics.mean(sub_scores)

    if avg > STYLE_CONSISTENCY_HIGH:
        direction = "ai-like"
        explanation = (
            "Quote style, indentation, and operator spacing are almost "
            "perfectly uniform (avg=%.2f); this level of polish is a weak "
            "AI-like signal." % avg
        )
    elif avg < STYLE_CONSISTENCY_LOW:
        direction = "human-like"
        explanation = (
            "Quote style, indentation, and/or operator spacing vary noticeably "
            "(avg=%.2f); this messiness is typical of human code." % avg
        )
    else:
        direction = "neutral"
        explanation = "Overall style consistency (avg=%.2f) is middling." % avg

    return {
        "name": "style_consistency_score",
        "value": round(avg, 4),
        "direction": direction,
        "explanation": explanation,
    }


def extract_code_features(code: str) -> List[dict]:
    """Run every code-mode feature extractor and return the list of results."""
    return [
        comment_density(code),
        comment_density_consistency(code),
        variable_naming_entropy(code),
        boilerplate_docstring_score(code),
        style_consistency_score(code),
    ]
