#!/usr/bin/env python3
"""
TakeoffBench CLI

Main entry point for the TakeoffBench benchmark toolkit.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_download(args):
    """Download benchmark data."""
    from cli.download import create_sample_dataset

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {args.split} split to {output_dir}...")
    create_sample_dataset(output_dir)


def cmd_evaluate(args):
    """Evaluate predictions against ground truth."""
    from evaluation.metrics import evaluate_benchmark, format_results

    # Load predictions
    with open(args.predictions) as f:
        predictions = json.load(f)

    # Handle single prediction vs list
    if isinstance(predictions, dict):
        predictions = [predictions]

    # Load ground truth
    gt_dir = Path(args.ground_truth)
    ground_truths = []

    if gt_dir.is_dir():
        for gt_file in gt_dir.glob("*.json"):
            with open(gt_file) as f:
                ground_truths.append(json.load(f))
    else:
        with open(gt_dir) as f:
            data = json.load(f)
            if isinstance(data, list):
                ground_truths = data
            else:
                ground_truths = [data]

    # Run evaluation
    results = evaluate_benchmark(predictions, ground_truths)

    # Output results
    print(format_results(results))

    if args.output:
        output_data = {
            "overall_score": results.mean_overall_score,
            "overall_score_ci": results.overall_score_ci,
            "element_recall": results.mean_element_recall,
            "element_precision": results.mean_element_precision,
            "quantity_mape": results.mean_quantity_mape,
            "classification_accuracy": results.mean_classification_accuracy,
            "csi_accuracy": results.mean_csi_accuracy,
            "num_projects": len(results.project_results),
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")


def cmd_run(args):
    """Run a baseline model."""
    from baselines.run_baseline import run_baseline

    run_baseline(
        model=args.model,
        input_dir=Path(args.input),
        output_file=Path(args.output),
        limit=args.limit
    )


def cmd_submit(args):
    """Submit predictions to leaderboard."""
    print("Submission endpoint coming soon!")
    print(f"Would submit: {args.predictions}")
    print(f"Model name: {args.model_name}")
    print("\nFor now, please open an issue on GitHub with your results.")


def main():
    parser = argparse.ArgumentParser(
        description="TakeoffBench - AI Benchmark for Construction Quantity Takeoff",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download sample data
  takeoffbench download --split val --output ./data

  # Run baseline model
  takeoffbench run --model claude --input ./images --output predictions.json

  # Evaluate predictions
  takeoffbench evaluate --predictions predictions.json --ground-truth ./data/ground_truth

  # Submit to leaderboard
  takeoffbench submit --predictions predictions.json --model-name "My Model"
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    dl_parser = subparsers.add_parser("download", help="Download benchmark data")
    dl_parser.add_argument("--split", choices=["train", "val", "test", "all"], default="val")
    dl_parser.add_argument("--output", default="./data", help="Output directory")
    dl_parser.set_defaults(func=cmd_download)

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate predictions")
    eval_parser.add_argument("--predictions", required=True, help="Predictions JSON file")
    eval_parser.add_argument("--ground-truth", required=True, help="Ground truth directory or file")
    eval_parser.add_argument("--output", help="Output file for results JSON")
    eval_parser.set_defaults(func=cmd_evaluate)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run baseline model")
    run_parser.add_argument("--model", required=True, help="Model name (claude, gpt-4o, gemini)")
    run_parser.add_argument("--input", required=True, help="Input images directory")
    run_parser.add_argument("--output", default="predictions.json", help="Output file")
    run_parser.add_argument("--limit", type=int, help="Max images to process")
    run_parser.set_defaults(func=cmd_run)

    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit to leaderboard")
    submit_parser.add_argument("--predictions", required=True, help="Predictions file")
    submit_parser.add_argument("--model-name", required=True, help="Name for leaderboard")
    submit_parser.set_defaults(func=cmd_submit)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
