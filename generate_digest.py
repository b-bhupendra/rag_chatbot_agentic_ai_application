"""
Script to generate LLM-ready text using gitingest.

Usage:
    # Generate clean codebase digest (recommended for LLM prompt context: ~31k tokens)
    python generate_digest.py

    # Include datasets and external skills
    python generate_digest.py --all

    # Custom output file
    python generate_digest.py -o my_prompt_context.txt
"""

import sys
import argparse
from pathlib import Path
from gitingest import ingest


def main():
    parser = argparse.ArgumentParser(description="Generate LLM-friendly codebase digest using gitingest.")
    parser.add_argument(
        "-o", "--output",
        default="digest.txt",
        help="Output file path (default: digest.txt)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all files including datasets and .agents/ skills"
    )
    parser.add_argument(
        "-s", "--source",
        default=".",
        help="Source directory (default: current directory)"
    )

    args = parser.parse_args()

    excludes = ["*.txt", "*.log", ".venv/*", "node_modules/*", "frontend/dist/*", "frontend/node_modules/*"]
    if not args.all:
        excludes.extend([".agents/*", "datasets/*"])

    print(f"Generating LLM digest for '{args.source}'...")
    summary, tree, content = ingest(args.source, exclude_patterns=excludes)

    print("\n" + "=" * 40)
    print(summary)
    print("=" * 40 + "\n")

    output_path = Path(args.output)
    full_output = f"# Directory Structure\n{tree}\n\n# File Contents\n{content}"
    output_path.write_text(full_output, encoding="utf-8")

    print(f"[SUCCESS] Digest written to: {output_path.resolve()} ({len(full_output):,} characters)")


if __name__ == "__main__":
    main()
