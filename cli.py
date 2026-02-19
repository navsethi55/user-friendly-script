#!/usr/bin/env python3
"""
Liquid Template Generator - Command Line Interface

Usage:
    python cli.py input.json                 # writes .liquid files to current directory
    python cli.py input.json -o output_dir   # writes to a specific directory
    python cli.py input.json --preview       # preview without writing files
"""

import argparse
import json
import sys
import time
from pathlib import Path

from liquid_generator.processor import process_json


def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-market Liquid templates from JSON content files.",
    )
    parser.add_argument(
        "input",
        help="Path to the JSON content file",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Directory to write .liquid files to (default: current directory)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview generated templates without writing files",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load JSON
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate structure
    try:
        _ = data["a"]["modules"][0]["content"]
    except (KeyError, IndexError, TypeError):
        print(
            'Error: unexpected JSON structure. Expected data["a"]["modules"][0]["content"].',
            file=sys.stderr,
        )
        sys.exit(1)

    # Process
    t0 = time.time()
    try:
        written, skipped = process_json(data)
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)

    elapsed = round(time.time() - t0, 3)

    if args.preview:
        # Preview mode: print to stdout
        for filename, liquid_content in written.items():
            print(f"--- {filename} ---")
            print(liquid_content)
            print()
        print(f"({len(written)} file(s) would be generated, {len(skipped)} skipped, {elapsed}s)")
    else:
        # Write files
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, liquid_content in written.items():
            out_path = output_dir / filename
            out_path.write_text(liquid_content, encoding="utf-8")

        print(f"Done in {elapsed}s")
        print("Files written:")
        for w in written:
            print(f"  - {w}")
        if skipped:
            print("Skipped (no data):")
            for s in skipped:
                print(f"  - {s}")


if __name__ == "__main__":
    main()
