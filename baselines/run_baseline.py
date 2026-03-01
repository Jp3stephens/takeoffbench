"""
TakeoffBench Baseline Model Runner

Runs VLM baselines on the benchmark and produces predictions.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.takeoff_schema import CSI_SECTIONS, CSI_DIVISIONS


TAKEOFF_PROMPT = """You are a professional construction estimator performing a quantity takeoff from an architectural floor plan.

Analyze this floor plan image and extract ALL quantities you can identify. Output a structured JSON takeoff schedule.

## Instructions:
1. Identify all doors, windows, and openings
2. Count plumbing fixtures (toilets, sinks, tubs, showers)
3. Note any cabinets or casework visible
4. Estimate room areas if dimensions are visible

## Output Format:
Return ONLY valid JSON matching this structure:
```json
{
  "project_id": "<filename>",
  "divisions": {
    "08 - Openings": {
      "sections": {
        "08 14 16 - Wood Doors": {
          "items": [
            {"description": "3'-0\" x 6'-8\" Interior Door", "quantity": 5, "unit": "EA"}
          ]
        }
      }
    }
  }
}
```

## CSI Divisions to use:
- 08 - Openings (doors, windows)
- 09 - Finishes (flooring, paint, ceilings)
- 12 - Furnishings (cabinets, countertops)
- 22 - Plumbing (fixtures)

## Important:
- Count EVERY door and window you see
- Include dimensions if visible (e.g., "3'-0\" x 6'-8\"")
- Use standard units: EA (each), LF (linear feet), SF (square feet)
- Be thorough - missing items hurts recall score

Output the JSON only, no other text."""


def encode_image(image_path: Path) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: Path) -> str:
    """Get media type from file extension."""
    ext = image_path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def run_claude(image_path: Path, project_id: str) -> dict:
    """Run Claude on a floor plan image."""
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()

    image_data = encode_image(image_path)
    media_type = get_image_media_type(image_path)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": TAKEOFF_PROMPT.replace("<filename>", project_id),
                    }
                ],
            }
        ],
    )

    # Extract JSON from response
    response_text = response.content[0].text

    # Try to parse JSON from response
    try:
        # Find JSON in response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    return {"project_id": project_id, "error": "Failed to parse response", "raw": response_text}


def run_openai(image_path: Path, project_id: str) -> dict:
    """Run GPT-4o on a floor plan image."""
    try:
        import openai
    except ImportError:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)

    client = openai.OpenAI()

    image_data = encode_image(image_path)
    media_type = get_image_media_type(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}",
                        },
                    },
                    {
                        "type": "text",
                        "text": TAKEOFF_PROMPT.replace("<filename>", project_id),
                    }
                ],
            }
        ],
    )

    response_text = response.choices[0].message.content

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    return {"project_id": project_id, "error": "Failed to parse response", "raw": response_text}


def run_gemini(image_path: Path, project_id: str) -> dict:
    """Run Gemini on a floor plan image."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: google-generativeai package not installed. Run: pip install google-generativeai")
        sys.exit(1)

    genai.configure()

    model = genai.GenerativeModel("gemini-1.5-pro")

    # Load image
    import PIL.Image
    image = PIL.Image.open(image_path)

    response = model.generate_content([
        TAKEOFF_PROMPT.replace("<filename>", project_id),
        image
    ])

    response_text = response.text

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    return {"project_id": project_id, "error": "Failed to parse response", "raw": response_text}


MODEL_RUNNERS = {
    "claude": run_claude,
    "claude-3.5-sonnet": run_claude,
    "gpt-4o": run_openai,
    "openai": run_openai,
    "gemini": run_gemini,
    "gemini-1.5-pro": run_gemini,
}


def run_baseline(
    model: str,
    input_dir: Path,
    output_file: Path,
    limit: Optional[int] = None
) -> list[dict]:
    """
    Run baseline model on all images in input directory.

    Args:
        model: Model name (claude, gpt-4o, gemini)
        input_dir: Directory containing floor plan images
        output_file: Where to save predictions
        limit: Max number of images to process

    Returns:
        List of prediction dictionaries
    """
    if model not in MODEL_RUNNERS:
        print(f"Error: Unknown model '{model}'. Available: {list(MODEL_RUNNERS.keys())}")
        sys.exit(1)

    runner = MODEL_RUNNERS[model]

    # Find all images
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    images = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if limit:
        images = images[:limit]

    print(f"Running {model} on {len(images)} images...")

    predictions = []
    for i, image_path in enumerate(images):
        project_id = image_path.stem
        print(f"  [{i+1}/{len(images)}] Processing {project_id}...")

        try:
            result = runner(image_path, project_id)
            predictions.append(result)
        except Exception as e:
            print(f"    Error: {e}")
            predictions.append({
                "project_id": project_id,
                "error": str(e)
            })

    # Save predictions
    with open(output_file, "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"\nSaved predictions to {output_file}")
    return predictions


def main():
    parser = argparse.ArgumentParser(description="Run baseline models on TakeoffBench")
    parser.add_argument(
        "--model",
        choices=list(MODEL_RUNNERS.keys()),
        required=True,
        help="Model to run"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Directory containing floor plan images"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("predictions.json"),
        help="Output file for predictions"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max number of images to process"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input directory '{args.input}' does not exist")
        sys.exit(1)

    run_baseline(args.model, args.input, args.output, args.limit)


if __name__ == "__main__":
    main()
