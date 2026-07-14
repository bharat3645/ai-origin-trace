"""Tests for the math/logic of code-mode feature extractors.

As in test_text_features.py: these assert that each heuristic's *math*
behaves as documented on constructed fixtures with known characteristics,
never that a snippet "really is" AI-written.
"""

from ai_origin_trace.code_features import (
    boilerplate_docstring_score,
    comment_density,
    comment_density_consistency,
    style_consistency_score,
    variable_naming_entropy,
)

UNIFORM_COMMENTS_CODE = "\n".join(
    [
        "# step 1",
        "x = 1",
        "# step 2",
        "y = 2",
        "# step 3",
        "z = 3",
        "# step 4",
        "w = 4",
        "# step 5",
        "v = 5",
        "# step 6",
        "u = 6",
        "# step 7",
        "t = 7",
        "# step 8",
        "s = 8",
        "# step 9",
        "r = 9",
        "# step 10",
        "q = 10",
        "# step 11",
        "p = 11",
        "# step 12",
        "o = 12",
    ]
)

BURSTY_COMMENTS_CODE = "\n".join(
    [
        "# setup section, lots of context needed here because this part is tricky",
        "# and here is more explanation of why we need this weird workaround",
        "# and one more line of rationale before the actual code starts",
        "a = 1",
        "b = 2",
        "c = 3",
        "d = 4",
        "e = 5",
        "f = 6",
        "g = 7",
        "h = 8",
        "i = 9",
        "j = 10",
        "k = 11",
        "# only one trailing comment way down here at the bottom of the file",
        "l = 12",
    ]
)


def test_comment_density_basic_ratio():
    result = comment_density(UNIFORM_COMMENTS_CODE)
    assert result["value"] == 0.5  # 12 comment lines / 24 non-blank lines
    assert result["direction"] == "neutral"


def test_comment_density_consistency_uniform_is_ai_like():
    result = comment_density_consistency(UNIFORM_COMMENTS_CODE, chunks=4)
    assert result["direction"] == "ai-like"
    assert result["value"] < 0.04


def test_comment_density_consistency_bursty_is_human_like():
    result = comment_density_consistency(BURSTY_COMMENTS_CODE, chunks=4)
    assert result["direction"] == "human-like"


UNIFORM_NAMING_CODE = "\n".join(
    "variable_number_{0} = {0}".format(i) for i in range(10)
)

MIXED_NAMING_CODE = "\n".join(
    [
        "i = 1",
        "userName = 2",
        "user_name = 3",
        "MAXVAL = 4",
        "j = 5",
        "totalCountValue = 6",
        "total_count_value = 7",
        "N = 8",
        "tmp = 9",
        "aVeryLongCamelCaseIdentifier = 10",
    ]
)


def test_variable_naming_entropy_uniform_is_ai_like():
    result = variable_naming_entropy(UNIFORM_NAMING_CODE)
    assert result["direction"] == "ai-like"
    assert result["value"] < 0.35


def test_variable_naming_entropy_mixed_is_human_like():
    result = variable_naming_entropy(MIXED_NAMING_CODE)
    assert result["direction"] == "human-like"
    assert result["value"] > 0.65


REPEATED_BOILERPLATE_DOCSTRINGS_CODE = '''
def foo(a, b):
    """Do the foo thing.

    Args:
        a: first thing.
        b: second thing.

    Returns:
        The result.
    """
    return a + b


def bar(a, b):
    """Do the bar thing.

    Args:
        a: first thing.
        b: second thing.

    Returns:
        The result.
    """
    return a - b


def baz(a, b):
    """Do the baz thing.

    Args:
        a: first thing.
        b: second thing.

    Returns:
        The result.
    """
    return a * b
'''

VARIED_DOCSTRINGS_CODE = '''
def foo(a, b):
    """Adds two numbers together.

    Returns:
        Sum of a and b.
    """
    return a + b


def bar(a, b):
    """Subtracts b from a.

    Raises:
        ValueError: never, this is just an example.
    """
    return a - b


def baz(a, b):
    """Multiplies two numbers.

    Note:
        Overflow is not handled.

    Example:
        baz(2, 3) -> 6
    """
    return a * b


def qux(a, b):
    """Divides a by b.

    Args:
        a: numerator.
        b: denominator.

    Returns:
        Quotient of a and b.
    """
    return a / b
'''


def test_boilerplate_docstring_score_repeated_template_is_ai_like():
    result = boilerplate_docstring_score(REPEATED_BOILERPLATE_DOCSTRINGS_CODE)
    assert result["direction"] == "ai-like"
    assert result["value"] > 0.7


def test_boilerplate_docstring_score_varied_templates_is_human_like():
    result = boilerplate_docstring_score(VARIED_DOCSTRINGS_CODE)
    assert result["direction"] == "human-like"
    assert result["value"] < 0.35


UNIFORM_STYLE_CODE = "\n".join(
    [
        'name_{0} = "value_{0}"'.format(i) for i in range(10)
    ]
)

MESSY_STYLE_CODE = "\n".join(
    [
        "name_0 = 'value_0'",
        'name_1="value_1"',
        "name_2 = 'value_2'",
        'name_3 = "value_3"',
        "name_4='value_4'",
        'name_5 = "value_5"',
        "name_6 = 'value_6'",
        'name_7="value_7"',
    ]
)


def test_style_consistency_score_uniform_is_ai_like():
    result = style_consistency_score(UNIFORM_STYLE_CODE)
    assert result["direction"] == "ai-like"
    assert result["value"] > 0.95


def test_style_consistency_score_messy_is_human_like():
    result = style_consistency_score(MESSY_STYLE_CODE)
    assert result["direction"] == "human-like"
    assert result["value"] < 0.75
