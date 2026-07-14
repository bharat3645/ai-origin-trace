# ai-origin-trace

> **SIGNAL, NOT PROOF.** ai-origin-trace produces a transparent, fully
> explainable, offline stylometric SIGNAL about text or code -- it does
> **not** and cannot prove that something was written by an AI or a human.
> It is **not** admissible as sole evidence in any academic-integrity,
> employment, or legal proceeding, and it is **not** a substitute for due
> process or a direct conversation with the author. Stylometric heuristics
> have **high false-positive and false-negative rates** -- this is inherent
> to the method, not a bug to be tuned away. Every run of the CLI prints
> this warning again; it is not optional decoration.

## Why this exists

There is growing (and messy) demand for signals on whether a piece of text
or code is likely AI-generated: academic-integrity offices, open-source
contribution policies, procurement reviews, and more. Most commercial "AI
detectors" (GPTZero and similar tools) are opaque black boxes: you send them
text, a network call happens, and you get back a single confident-looking
score with no explanation of what produced it. That opacity has caused real
harm -- documented false accusations against students, including
disproportionate false-positive rates for non-native English speakers, and
disciplinary action taken on the strength of a number nobody could
interrogate.

**ai-origin-trace takes the opposite approach.** It trades detection
accuracy for full transparency:

- **Fully offline.** No API calls, no third-party detection service, no
  network dependency of any kind for its core analysis.
- **Fully explainable.** Every feature is a documented, auditable heuristic
  you can read the source of in five minutes. No hidden model weights.
- **Never a single black-box score.** Output is a per-feature breakdown --
  raw value, a labeled direction (`ai-like` / `human-like` / `neutral` /
  `inconclusive`), and a plain-English explanation -- plus a coarse,
  clearly-hedged overall lean (e.g. *"weak lean toward ai-like patterns"*).
  The tool will never say "73% AI-generated"; that phrasing is explicitly
  banned from its output because it implies a false precision that
  stylometry cannot support.
- **Explicitly framed as a discussion-starter for a human reviewer**, never
  a verdict.

## Install

```bash
git clone https://github.com/bharat3645/ai-origin-trace.git
cd ai-origin-trace
pip install -r requirements.txt   # only pytest is required; see requirements.txt for optional extras
```

Requires Python 3.8+. No required third-party dependencies for the core
CLI -- `nltk` and `anthropic` are optional (see below).

## Usage

```bash
python -m ai_origin_trace analyze path/to/file.txt
python -m ai_origin_trace analyze path/to/script.py --mode code
python -m ai_origin_trace analyze path/to/file.txt --json
python -m ai_origin_trace --disclaimer
```

`--mode` defaults to auto-detection from the file extension (common code
extensions map to `code`; everything else to `text`). The ethical
disclaimer banner is printed before every result by default; suppress it
(not recommended) with `--quiet-banner`.

### Sample output (text mode)

```
$ python -m ai_origin_trace analyze essay.txt --quiet-banner

Mode: text
------------------------------------------------------------------------------
FEATURE                      VALUE      DIRECTION    EXPLANATION
------------------------------------------------------------------------------
burstiness                   0.1829     ai-like      Sentence lengths are very uniform (CV=0.18, below 0.35); generated text often has less natural rhythm variation.
function_word_ratio          0.4286     neutral      Function-word ratio (0.43) falls within the typical human baseline (0.40-0.60).
repetition_score             0.0        human-like   Only 0.0% of 4-grams repeat; low phrase repetition is typical of freely composed human writing.
vocabulary_richness          0.6857     neutral      Moving-window vocabulary richness (MATTR=0.69) is in a middling range.
------------------------------------------------------------------------------
Overall signal: inconclusive
Reminder: this is a discussion-starting SIGNAL for a human reviewer, not proof of AI or human authorship. Do not use it as sole evidence.
```

Notice that even when several features individually lean `ai-like` or
`human-like`, the overall line stays hedged (`inconclusive`, `weak lean`,
etc.) rather than collapsing everything into a confident single verdict.

## What it measures

**Text mode:**
- **Burstiness** -- coefficient of variation of sentence length. Very
  uniform sentence lengths are a weak ai-like signal; human writing tends
  to mix short and long sentences.
- **Function-word ratio** -- ratio of common function words (the, of, and,
  to, ...) to total words, compared against a fixed, documented "typical
  human baseline" of 0.40-0.60.
- **Repetition/template score** -- rate of repeated 4-grams, a weak signal
  of templated phrasing.
- **Vocabulary richness** -- Moving Average Type-Token Ratio (MATTR): a
  sliding window of unique-words-per-window, averaged across the text. This
  fixes the classic bug where raw type-token ratio shrinks mechanically as
  text gets longer, so texts of different lengths stay comparable.

**Code mode** (language-agnostic heuristics; a couple of checks are
Python-flavored, e.g. triple-quoted docstrings, and degrade gracefully on
other languages):
- **Comment-density ratio and its consistency** -- suspiciously *uniform*
  comment density across a file (not the raw ratio itself) is the actual
  weak signal.
- **Variable-naming entropy** -- Shannon entropy over identifier
  naming-convention buckets (snake_case, camelCase, ALL_CAPS, single-letter,
  other). Very low entropy (one convention used everywhere) is a weak
  ai-like signal; humans routinely mix conventions.
- **Boilerplate docstring detection** -- regex-based detection of repeated
  `Args:`/`Returns:`/`Raises:` scaffolding reused verbatim across many
  functions.
- **Style-consistency score** -- consistency of quote style, indentation,
  and spacing around `=`; near-perfect uniformity is a weak ai-like signal.

Tokenization is a plain regex fallback by default. If `nltk` happens to be
installed *and* its `punkt` data has been downloaded, sentence splitting
opportunistically upgrades to nltk's tokenizer -- but a missing install or a
missing corpus download will never break the tool; every nltk call is
wrapped so it silently falls back to the regex tokenizer.

## Limitations & Responsible Use

- **This is a signal, not a verdict.** Treat every result as a
  conversation-starter with the author, not a conclusion about them.
- **High false-positive and false-negative rates are expected and
  inherent to stylometry**, not implementation bugs. Terse technical
  writing, non-native English phrasing, heavily-edited human prose, tightly
  styled/linted codebases, and many other ordinary situations can trigger
  "ai-like" signals. Verbose or idiosyncratic AI output can trigger
  "human-like" signals. Neither outcome is reliable in isolation.
- **Never use this as the sole piece of evidence** in an academic-integrity
  case, a hiring decision, a performance review, or any other consequential
  decision about a person. Always corroborate with a direct conversation
  with the author first.
- **This tool refuses to output a confidence percentage** (e.g. "82% AI
  generated"). If you see that phrasing anywhere claiming to come from this
  tool, it has been modified from its intended design.
- The fixed thresholds and baselines used throughout (e.g. the 0.40-0.60
  function-word baseline, the MATTR cutoffs) are documented, reasonable
  engineering choices, not the output of large-scale empirical calibration
  against a labeled corpus of known AI/human text. Treat them as
  transparent defaults you can inspect and adjust, not ground truth.

## Optional narrative-explanation layer

`requirements.txt` lists `anthropic` as an optional dependency for a
narrative-explanation layer that can turn the per-feature breakdown into a
plain-English paragraph via the Claude API. It follows a strict
no-key-fallback pattern: it is never invoked unless you explicitly opt in
and set `ANTHROPIC_API_KEY` in your environment; with no key set, the CLI's
core analysis works exactly as documented above with zero network calls.

## Testing

```bash
pip install pytest
pytest
```

Every feature extractor has tests built from fixtures with **known**
characteristics (e.g. one highly uniform/repetitive snippet, one clearly
varied/messy snippet), asserting that the heuristic's *math* moves in the
expected direction -- not that any fixture "really is" AI-written, which is
a claim this project deliberately does not make and cannot test. The moving
average TTR calculation is also checked against a hand-computed example,
and the aggregator's direction-labeling logic is tested directly.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2026 Bharat Singh Parihar.
