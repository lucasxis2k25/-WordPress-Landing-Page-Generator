from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .pipeline import GoldenMismatch, bootstrap, run_products


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m mapping")
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = sub.add_parser("bootstrap", help="Read the XLSX once and create the Parquet snapshot/cache")
    bootstrap_parser.add_argument("--input", required=True, help="Reference XLSX")
    bootstrap_parser.add_argument("--data-dir", default="data")
    bootstrap_parser.add_argument("--golden-dir", default="tests/golden")

    run_parser = sub.add_parser("run", help="Run only explicitly requested products from Parquet")
    run_parser.add_argument("--input", required=True, help="Normalized Parquet snapshot")
    run_parser.add_argument("--data-dir", default="data")
    run_parser.add_argument("--golden-dir", default="tests/golden")
    run_parser.add_argument("--products", nargs="+", required=True)
    run_parser.add_argument("--incremental", action="store_true", default=False)
    run_parser.add_argument("--publish-static", action="store_true", default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "bootstrap":
        result = bootstrap(args.input, args.data_dir, args.golden_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "run":
        if not args.incremental:
            raise SystemExit("Refusing non-incremental execution; pass --incremental")
        if any(product.casefold() == "all" for product in args.products):
            raise SystemExit("Phase 1 is pilot-only; do not process all products yet")
        try:
            result = run_products(args.input, args.data_dir, args.golden_dir, args.products, args.publish_static)
        except GoldenMismatch as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps({"manifest": result["manifest"], "research_queue": result["research_queue"]}, ensure_ascii=False, indent=2))
        return 0
    return 1
