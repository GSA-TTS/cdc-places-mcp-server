#!/usr/bin/env python3
"""CLI entry point for MCP server evaluation."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from mcp_data_check import run_evaluation

# Load environment variables from .env file
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate MCP server accuracy against known questions and answers"
    )
    parser.add_argument(
        "server_url",
        nargs="?",
        default=os.environ.get("MCP_SERVER_URL"),
        help="URL of the MCP server to evaluate (default: MCP_SERVER_URL env var)"
    )
    parser.add_argument(
        "-q", "--questions",
        default=None,
        help="Path to questions CSV file (default: eval/questions.csv)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory for results (default: eval/results)"
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)"
    )
    parser.add_argument(
        "-n", "--server-name",
        default="nih-reporter",
        help="Name for the MCP server (default: nih-reporter)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress"
    )

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Validate server URL
    if not args.server_url:
        print("Error: No server URL provided. Set MCP_SERVER_URL environment variable or pass as argument.", file=sys.stderr)
        sys.exit(1)

    # Determine paths
    eval_dir = Path(__file__).parent
    questions_path = Path(args.questions) if args.questions else eval_dir / "questions.csv"
    output_dir = Path(args.output) if args.output else eval_dir / "results"

    # Validate questions file exists
    if not questions_path.exists():
        print(f"Error: Questions file not found: {questions_path}", file=sys.stderr)
        sys.exit(1)

    # Run evaluation
    print(f"Loading questions from {questions_path}...")
    print(f"Evaluating against {args.server_url}...")
    print("-" * 50)

    results = run_evaluation(
        questions_filepath=questions_path,
        api_key=api_key,
        server_url=args.server_url,
        model=args.model,
        server_name=args.server_name,
        verbose=args.verbose
    )

    summary = results["summary"]

    # Print summary
    print("-" * 50)
    print("\nEvaluation Summary")
    print("=" * 50)
    print(f"Total questions: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate']:.1%}")

    if summary.get("by_eval_type"):
        print("\nBy evaluation type:")
        for eval_type, stats in summary["by_eval_type"].items():
            type_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {eval_type}: {stats['passed']}/{stats['total']} ({type_rate:.1%})")

    # Print failed questions
    failed_results = [r for r in results["results"] if not r["passed"]]
    if failed_results:
        print(f"\nFailed questions ({len(failed_results)}):")
        for r in failed_results:
            print(f"\n  Q: {r['question'][:80]}...")
            print(f"  Expected: {r['expected_answer'][:50]}...")
            if r.get("error"):
                print(f"  Error: {r['error']}")
            else:
                print(f"  Details: {r.get('details', {}).get('details', 'N/A')}")

    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"eval_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Exit with non-zero if any failures
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
