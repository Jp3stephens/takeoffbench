"""
TakeoffBench Evaluation Metrics

Computes scores comparing predicted takeoff schedules against ground truth.
"""

import json
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class EvaluationResult:
    """Results from evaluating a single prediction."""

    project_id: str
    element_recall: float  # Did we find all elements?
    element_precision: float  # Of elements found, how many are correct?
    quantity_mape: float  # Mean Absolute Percentage Error on quantities
    classification_accuracy: float  # Are types/specs correct?
    csi_accuracy: float  # Are CSI codes correct?
    overall_score: float  # Weighted combination

    # Detailed breakdowns
    matched_items: int
    predicted_items: int
    ground_truth_items: int
    quantity_errors: list[dict]


@dataclass
class BenchmarkResult:
    """Aggregate results across all predictions."""

    mean_element_recall: float
    mean_element_precision: float
    mean_quantity_mape: float
    mean_classification_accuracy: float
    mean_csi_accuracy: float
    mean_overall_score: float

    # Confidence intervals
    overall_score_ci: float

    # Per-project results
    project_results: list[EvaluationResult]


def normalize_description(desc: str) -> str:
    """Normalize a description for fuzzy matching."""
    # Lowercase
    desc = desc.lower()

    # Normalize dimensions (3'-0" -> 3-0, 3'0" -> 3-0, 36" -> 36)
    desc = re.sub(r"(\d+)['\"]?\s*-?\s*(\d+)['\"]?", r"\1-\2", desc)

    # Remove common filler words
    for word in ["the", "a", "an", "with", "and", "or"]:
        desc = re.sub(rf"\b{word}\b", "", desc)

    # Normalize whitespace
    desc = " ".join(desc.split())

    return desc


def extract_dimensions(desc: str) -> Optional[tuple[float, float]]:
    """Extract width x height dimensions from description."""
    # Match patterns like "3'-0\" x 6'-8\"" or "36 x 80"
    pattern = r"(\d+)['\"]?\s*-?\s*(\d*)['\"]?\s*[xX×]\s*(\d+)['\"]?\s*-?\s*(\d*)['\"]?"
    match = re.search(pattern, desc)

    if match:
        w_ft = int(match.group(1))
        w_in = int(match.group(2)) if match.group(2) else 0
        h_ft = int(match.group(3))
        h_in = int(match.group(4)) if match.group(4) else 0

        width = w_ft * 12 + w_in if w_ft < 20 else w_ft  # Assume inches if > 20
        height = h_ft * 12 + h_in if h_ft < 20 else h_ft

        return (width, height)

    return None


def match_items(pred_items: list[dict], gt_items: list[dict]) -> list[tuple[dict, dict, float]]:
    """Match predicted items to ground truth items using fuzzy matching."""
    matches = []
    used_gt = set()

    for pred in pred_items:
        pred_norm = normalize_description(pred.get("description", ""))
        pred_dims = extract_dimensions(pred.get("description", ""))

        best_match = None
        best_score = 0.0

        for i, gt in enumerate(gt_items):
            if i in used_gt:
                continue

            gt_norm = normalize_description(gt.get("description", ""))
            gt_dims = extract_dimensions(gt.get("description", ""))

            # Compute similarity score
            score = 0.0

            # Check if same CSI section
            if pred.get("section") == gt.get("section"):
                score += 0.3

            # Check dimension match
            if pred_dims and gt_dims:
                if pred_dims == gt_dims:
                    score += 0.4
                elif abs(pred_dims[0] - gt_dims[0]) <= 2 and abs(pred_dims[1] - gt_dims[1]) <= 2:
                    score += 0.2

            # Check description overlap
            pred_words = set(pred_norm.split())
            gt_words = set(gt_norm.split())
            if pred_words and gt_words:
                overlap = len(pred_words & gt_words) / len(pred_words | gt_words)
                score += 0.3 * overlap

            if score > best_score:
                best_score = score
                best_match = (i, gt)

        if best_match and best_score >= 0.3:  # Threshold for match
            matches.append((pred, best_match[1], best_score))
            used_gt.add(best_match[0])

    return matches


def compute_quantity_error(pred_qty: float, gt_qty: float) -> float:
    """Compute absolute percentage error for quantity."""
    if gt_qty == 0:
        return 1.0 if pred_qty > 0 else 0.0
    return abs(pred_qty - gt_qty) / gt_qty


def evaluate_single(
    prediction: dict,
    ground_truth: dict,
    weights: Optional[dict] = None
) -> EvaluationResult:
    """
    Evaluate a single prediction against ground truth.

    Args:
        prediction: Predicted takeoff schedule
        ground_truth: Ground truth takeoff schedule
        weights: Optional custom weights for scoring

    Returns:
        EvaluationResult with detailed metrics
    """
    if weights is None:
        weights = {
            "element_recall": 0.40,
            "quantity_accuracy": 0.30,
            "classification": 0.20,
            "csi_mapping": 0.10,
        }

    project_id = ground_truth.get("project_id", "unknown")

    # Flatten both schedules
    pred_items = flatten_schedule(prediction)
    gt_items = flatten_schedule(ground_truth)

    # Match items
    matches = match_items(pred_items, gt_items)

    # Compute metrics
    matched_count = len(matches)
    pred_count = len(pred_items)
    gt_count = len(gt_items)

    # Element Recall: What fraction of GT items did we find?
    element_recall = matched_count / gt_count if gt_count > 0 else 0.0

    # Element Precision: What fraction of predicted items are correct?
    element_precision = matched_count / pred_count if pred_count > 0 else 0.0

    # Quantity MAPE: Average percentage error on matched items
    quantity_errors = []
    for pred, gt, _ in matches:
        pred_qty = pred.get("quantity", 0)
        gt_qty = gt.get("quantity", 0)
        error = compute_quantity_error(pred_qty, gt_qty)
        quantity_errors.append({
            "predicted": pred_qty,
            "ground_truth": gt_qty,
            "error": error,
            "description": gt.get("description", "")
        })

    quantity_mape = (
        sum(e["error"] for e in quantity_errors) / len(quantity_errors)
        if quantity_errors else 1.0
    )
    # Convert MAPE to accuracy (1 - MAPE, clamped to 0-1)
    quantity_accuracy = max(0, 1 - quantity_mape)

    # Classification accuracy: For matched items, are descriptions correct?
    classification_correct = 0
    for pred, gt, match_score in matches:
        if match_score >= 0.5:  # Good match
            classification_correct += 1
    classification_accuracy = (
        classification_correct / matched_count if matched_count > 0 else 0.0
    )

    # CSI accuracy: For matched items, are CSI codes correct?
    csi_correct = 0
    for pred, gt, _ in matches:
        if pred.get("section") == gt.get("section"):
            csi_correct += 1
    csi_accuracy = csi_correct / matched_count if matched_count > 0 else 0.0

    # Overall score (weighted)
    overall_score = (
        weights["element_recall"] * element_recall +
        weights["quantity_accuracy"] * quantity_accuracy +
        weights["classification"] * classification_accuracy +
        weights["csi_mapping"] * csi_accuracy
    )

    return EvaluationResult(
        project_id=project_id,
        element_recall=element_recall,
        element_precision=element_precision,
        quantity_mape=quantity_mape,
        classification_accuracy=classification_accuracy,
        csi_accuracy=csi_accuracy,
        overall_score=overall_score,
        matched_items=matched_count,
        predicted_items=pred_count,
        ground_truth_items=gt_count,
        quantity_errors=quantity_errors,
    )


def flatten_schedule(schedule: dict) -> list[dict]:
    """Flatten a nested takeoff schedule to a list of items."""
    items = []

    # Handle different formats
    if "divisions" in schedule:
        for div_name, division in schedule.get("divisions", {}).items():
            if isinstance(division, dict):
                for section_code, section in division.get("sections", {}).items():
                    if isinstance(section, dict):
                        for item in section.get("items", []):
                            items.append({
                                "division": div_name,
                                "section": section_code,
                                **item
                            })
    elif "takeoff" in schedule:
        # Alternative flat format
        for div_name, sections in schedule.get("takeoff", {}).items():
            if isinstance(sections, dict):
                for section_code, section_items in sections.items():
                    if isinstance(section_items, list):
                        for item in section_items:
                            items.append({
                                "division": div_name,
                                "section": section_code,
                                **item
                            })

    return items


def evaluate_benchmark(
    predictions: list[dict],
    ground_truths: list[dict],
    weights: Optional[dict] = None
) -> BenchmarkResult:
    """
    Evaluate all predictions against ground truths.

    Args:
        predictions: List of predicted takeoff schedules
        ground_truths: List of ground truth schedules
        weights: Optional custom weights

    Returns:
        BenchmarkResult with aggregate metrics
    """
    # Match predictions to ground truths by project_id
    gt_by_id = {gt.get("project_id"): gt for gt in ground_truths}

    results = []
    for pred in predictions:
        project_id = pred.get("project_id")
        if project_id in gt_by_id:
            result = evaluate_single(pred, gt_by_id[project_id], weights)
            results.append(result)

    if not results:
        raise ValueError("No predictions matched ground truth project IDs")

    # Compute aggregates
    n = len(results)
    mean_recall = sum(r.element_recall for r in results) / n
    mean_precision = sum(r.element_precision for r in results) / n
    mean_mape = sum(r.quantity_mape for r in results) / n
    mean_classification = sum(r.classification_accuracy for r in results) / n
    mean_csi = sum(r.csi_accuracy for r in results) / n
    mean_overall = sum(r.overall_score for r in results) / n

    # Compute confidence interval (95% CI using standard error)
    if n > 1:
        variance = sum((r.overall_score - mean_overall) ** 2 for r in results) / (n - 1)
        std_error = (variance / n) ** 0.5
        ci = 1.96 * std_error
    else:
        ci = 0.0

    return BenchmarkResult(
        mean_element_recall=mean_recall,
        mean_element_precision=mean_precision,
        mean_quantity_mape=mean_mape,
        mean_classification_accuracy=mean_classification,
        mean_csi_accuracy=mean_csi,
        mean_overall_score=mean_overall,
        overall_score_ci=ci,
        project_results=results,
    )


def format_results(result: BenchmarkResult) -> str:
    """Format benchmark results for display."""
    lines = [
        "=" * 60,
        "TakeoffBench Evaluation Results",
        "=" * 60,
        "",
        f"Overall Score: {result.mean_overall_score * 100:.1f}% (±{result.overall_score_ci * 100:.1f}%)",
        "",
        "Component Scores:",
        f"  Element Recall:      {result.mean_element_recall * 100:.1f}%",
        f"  Element Precision:   {result.mean_element_precision * 100:.1f}%",
        f"  Quantity MAPE:       {result.mean_quantity_mape * 100:.1f}%",
        f"  Classification:      {result.mean_classification_accuracy * 100:.1f}%",
        f"  CSI Mapping:         {result.mean_csi_accuracy * 100:.1f}%",
        "",
        f"Evaluated {len(result.project_results)} projects",
        "=" * 60,
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    # Test with example data
    ground_truth = {
        "project_id": "test_001",
        "divisions": {
            "08 - Openings": {
                "sections": {
                    "08 14 16": {
                        "items": [
                            {"description": "3'-0\" x 6'-8\" HC Door", "quantity": 6, "unit": "EA"},
                            {"description": "2'-8\" x 6'-8\" HC Door", "quantity": 4, "unit": "EA"},
                        ]
                    },
                    "08 52 00": {
                        "items": [
                            {"description": "3'-0\" x 4'-0\" DH Window", "quantity": 8, "unit": "EA"},
                        ]
                    }
                }
            }
        }
    }

    prediction = {
        "project_id": "test_001",
        "divisions": {
            "08 - Openings": {
                "sections": {
                    "08 14 16": {
                        "items": [
                            {"description": "3-0 x 6-8 Hollow Core Door", "quantity": 5, "unit": "EA"},
                            {"description": "2-8 x 6-8 Hollow Core Door", "quantity": 4, "unit": "EA"},
                        ]
                    },
                    "08 52 00": {
                        "items": [
                            {"description": "3-0 x 4-0 Double Hung Window", "quantity": 7, "unit": "EA"},
                        ]
                    }
                }
            }
        }
    }

    result = evaluate_single(prediction, ground_truth)
    print(f"Overall Score: {result.overall_score:.2%}")
    print(f"Element Recall: {result.element_recall:.2%}")
    print(f"Quantity MAPE: {result.quantity_mape:.2%}")
