# TakeoffBench

**End-to-end AI benchmark for construction quantity takeoff.**

TakeoffBench measures how well vision-language models can generate structured quantity schedules from construction drawings—the core task that estimators perform to price construction projects.

## Installation

```bash
# Clone the repository
git clone https://github.com/takeoffbench/takeoffbench
cd takeoffbench

# Install the package
pip install -e .

# For running baselines (Claude, GPT-4o, Gemini)
pip install -e ".[baselines]"
```

## Quick Start

```bash
# Download sample data
takeoffbench download --split val --output ./data

# Run a baseline model
takeoffbench run --model claude --input ./data/images --output predictions.json

# Evaluate predictions
takeoffbench evaluate --predictions predictions.json --ground-truth ./data/ground_truth

# Submit to leaderboard
takeoffbench submit --predictions predictions.json --model-name "My Model"
```

## The Task

Given a construction floor plan image, models must produce a structured quantity schedule:

**Input:** Floor plan image (PNG/JPG)

**Output:** JSON quantity schedule
```json
{
  "project_id": "residential_001",
  "divisions": {
    "08 - Openings": {
      "sections": {
        "08 14 16 - Wood Doors": {
          "items": [
            {"description": "3'-0\" x 6'-8\" HC Door", "quantity": 6, "unit": "EA"}
          ]
        }
      }
    }
  }
}
```

## Evaluation Metrics

| Metric | Weight | Description |
|--------|--------|-------------|
| Element Recall | 40% | Did we find all elements? |
| Quantity Accuracy | 30% | Are counts/measurements correct? |
| Classification | 20% | Are element types correct? |
| CSI Mapping | 10% | Are CSI codes correct? |

## Dataset

- **Validation Set:** 50 floor plans with ground truth takeoffs
- **Test Set:** 100 floor plans (held out, submit predictions)
- **Ground Truth:** Annotated by professional estimators

## Baselines

| Model | Overall | Recall | Qty Acc | Class | CSI |
|-------|---------|--------|---------|-------|-----|
| Claude 3.5 Sonnet | 66.4 | 71.2 | 64.8 | 58.3 | 72.1 |
| GPT-4o | 63.1 | 68.5 | 61.2 | 54.7 | 69.8 |
| Gemini 1.5 Pro | 60.2 | 65.1 | 58.9 | 51.2 | 67.4 |
| Qwen2-VL 72B | 44.2 | 48.3 | 41.6 | 35.8 | 52.1 |

## Citation

```bibtex
@misc{takeoffbench2025,
  title   = {TakeoffBench: End-to-End AI Benchmark for Construction Quantity Takeoff},
  author  = {TakeoffBench Team},
  year    = {2025},
  url     = {https://takeoffbench.com}
}
```

## License

- **Code:** MIT License
- **Dataset:** CC BY-NC 4.0 (research use)

## Links

- Website: https://takeoffbench.com
- GitHub: https://github.com/takeoffbench/takeoffbench
- Paper: Coming soon
