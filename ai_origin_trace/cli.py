"""Command-line entrypoint for ai-origin-trace.

Usage:
    python -m ai_origin_trace analyze <file> [--mode text|code] [--json]
    python -m ai_origin_trace analyze <file> --quiet-banner
    python -m ai_origin_trace --disclaimer

The ethical disclaimer banner is printed on every invocation by default --
this is a hard requirement of this tool, not optional polish. It can only be
suppressed (not recommended) with --quiet-banner, and never on the
--disclaimer path itself.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import disclaimer
from .aggregator import build_report, format_report_text
from .code_features import extract_code_features
from .text_features import extract_text_features

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt", ".scala", ".sh",
}


def _guess_mode(path: str) -> str:
    lower = path.lower()
    for ext in CODE_EXTENSIONS:
        if lower.endswith(ext):
            return "code"
    return "text"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai_origin_trace",
        description=(
            "Transparent, offline stylometric AI-vs-human authorship SIGNAL "
            "estimator. Not an AI detector. See --disclaimer."
        ),
    )
    parser.add_argument(
        "--disclaimer",
        action="store_true",
        help="Print the full ethical-use disclaimer and exit.",
    )

    subparsers = parser.add_subparsers(dest="command")
    analyze = subparsers.add_parser("analyze", help="Analyze a text or code file for stylometric signals.")
    analyze.add_argument("file", help="Path to the file to analyze.")
    analyze.add_argument(
        "--mode",
        choices=["text", "code"],
        default=None,
        help="Force analysis mode. Defaults to auto-detect from file extension.",
    )
    analyze.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a text table.")
    analyze.add_argument(
        "--quiet-banner",
        action="store_true",
        help="Suppress the ethical disclaimer banner (not recommended).",
    )

    return parser


def run_analyze(args) -> int:
    if not args.quiet_banner:
        disclaimer.print_banner(full=False)

    try:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError as exc:
        print("Error reading file %r: %s" % (args.file, exc), file=sys.stderr)
        return 1

    mode = args.mode or _guess_mode(args.file)
    features = extract_code_features(content) if mode == "code" else extract_text_features(content)
    report = build_report(features, mode)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print()
        print(format_report_text(report))

    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.disclaimer:
        disclaimer.print_banner(full=True)
        return 0

    if args.command == "analyze":
        return run_analyze(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
