"""Command line entry: python -m assettags INPUT.csv [-o labels.pdf]."""

from __future__ import annotations

import argparse
import sys

from .labels import build_pdf, read_labels


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns 0 on success, 1 on bad input."""
    parser = argparse.ArgumentParser(prog="assettags", description="QR asset label sheet generator")
    parser.add_argument("input", help="CSV with asset_id, name, building, location")
    parser.add_argument("-o", "--output", default="labels.pdf")
    args = parser.parse_args(argv)
    try:
        labels = read_labels(args.input)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if not labels:
        print("Error: no labels in input", file=sys.stderr)
        return 1
    pages = build_pdf(labels, args.output)
    print(f"Wrote {args.output}: {len(labels)} labels, {pages} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
