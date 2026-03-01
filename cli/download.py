"""
TakeoffBench Data Download CLI

Downloads and prepares the benchmark dataset.
"""

import argparse
import json
import os
import urllib.request
import zipfile
from pathlib import Path


# Sample floor plans from public sources
SAMPLE_DATA_URL = "https://github.com/CubiCasa/CubiCasa5k/raw/master/data/test.zip"

DATA_DIR = Path(__file__).parent.parent / "data"


def download_file(url: str, dest: Path) -> None:
    """Download a file with progress indication."""
    print(f"Downloading {url}...")

    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size) if total_size > 0 else 0
        print(f"\r  Progress: {percent}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, report_progress)
    print()


def create_sample_dataset(output_dir: Path) -> None:
    """
    Create a sample dataset for testing.

    Since real construction drawing datasets require licensing,
    we create a minimal sample dataset for development/testing.
    """
    print("Creating sample dataset...")

    samples_dir = output_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # Create sample ground truth files
    sample_projects = [
        {
            "project_id": "sample_001",
            "name": "Single Family Residence",
            "drawing_sheets": ["A-101"],
            "divisions": {
                "08 - Openings": {
                    "sections": {
                        "08 14 16 - Wood Doors": {
                            "items": [
                                {"description": "3'-0\" x 6'-8\" HC Interior Door", "quantity": 6, "unit": "EA"},
                                {"description": "2'-8\" x 6'-8\" HC Interior Door", "quantity": 2, "unit": "EA"},
                                {"description": "3'-0\" x 6'-8\" Solid Core Entry Door", "quantity": 1, "unit": "EA"},
                            ]
                        },
                        "08 52 00 - Wood Windows": {
                            "items": [
                                {"description": "3'-0\" x 4'-0\" Double Hung Window", "quantity": 6, "unit": "EA"},
                                {"description": "4'-0\" x 5'-0\" Double Hung Window", "quantity": 2, "unit": "EA"},
                                {"description": "6'-0\" x 4'-0\" Sliding Window", "quantity": 1, "unit": "EA"},
                            ]
                        }
                    }
                },
                "09 - Finishes": {
                    "sections": {
                        "09 29 00 - Gypsum Board": {
                            "items": [
                                {"description": "5/8\" Type X GWB on Walls", "quantity": 2450, "unit": "SF"},
                                {"description": "1/2\" GWB on Ceilings", "quantity": 1850, "unit": "SF"},
                            ]
                        }
                    }
                },
                "12 - Furnishings": {
                    "sections": {
                        "12 32 00 - Casework": {
                            "items": [
                                {"description": "Base Cabinet 24\" x 34.5\"", "quantity": 8, "unit": "LF"},
                                {"description": "Wall Cabinet 24\" x 30\"", "quantity": 6, "unit": "LF"},
                                {"description": "Vanity Cabinet 36\"", "quantity": 2, "unit": "EA"},
                            ]
                        }
                    }
                }
            }
        },
        {
            "project_id": "sample_002",
            "name": "Small Commercial Office",
            "drawing_sheets": ["A-101", "A-102"],
            "divisions": {
                "08 - Openings": {
                    "sections": {
                        "08 11 13 - HM Doors": {
                            "items": [
                                {"description": "3'-0\" x 7'-0\" HM Door w/ Frame", "quantity": 12, "unit": "EA"},
                                {"description": "Pair 3'-0\" x 7'-0\" HM Doors", "quantity": 2, "unit": "EA"},
                            ]
                        },
                        "08 41 13 - Aluminum Entrances": {
                            "items": [
                                {"description": "3'-0\" x 7'-0\" Storefront Entry", "quantity": 2, "unit": "EA"},
                            ]
                        },
                        "08 51 13 - Aluminum Windows": {
                            "items": [
                                {"description": "4'-0\" x 5'-0\" Fixed Window", "quantity": 16, "unit": "EA"},
                                {"description": "6'-0\" x 6'-0\" Storefront Window", "quantity": 4, "unit": "EA"},
                            ]
                        }
                    }
                },
                "09 - Finishes": {
                    "sections": {
                        "09 29 00 - Gypsum Board": {
                            "items": [
                                {"description": "5/8\" Type X GWB on Walls", "quantity": 8500, "unit": "SF"},
                            ]
                        },
                        "09 51 00 - Acoustical Ceilings": {
                            "items": [
                                {"description": "2x4 ACT Ceiling System", "quantity": 4200, "unit": "SF"},
                            ]
                        },
                        "09 65 00 - Resilient Flooring": {
                            "items": [
                                {"description": "VCT Flooring", "quantity": 3800, "unit": "SF"},
                                {"description": "Rubber Base", "quantity": 920, "unit": "LF"},
                            ]
                        }
                    }
                },
                "22 - Plumbing": {
                    "sections": {
                        "22 42 00 - Commercial Fixtures": {
                            "items": [
                                {"description": "Water Closet, Floor Mount", "quantity": 8, "unit": "EA"},
                                {"description": "Lavatory, Wall Mount", "quantity": 6, "unit": "EA"},
                                {"description": "Urinal, Wall Mount", "quantity": 4, "unit": "EA"},
                                {"description": "Break Room Sink", "quantity": 1, "unit": "EA"},
                            ]
                        }
                    }
                }
            }
        },
        {
            "project_id": "sample_003",
            "name": "Apartment Unit",
            "drawing_sheets": ["A-101"],
            "divisions": {
                "08 - Openings": {
                    "sections": {
                        "08 14 16 - Wood Doors": {
                            "items": [
                                {"description": "3'-0\" x 6'-8\" Flush Wood Door", "quantity": 4, "unit": "EA"},
                                {"description": "2'-6\" x 6'-8\" Flush Wood Door", "quantity": 2, "unit": "EA"},
                            ]
                        },
                        "08 32 13 - Sliding Glass Doors": {
                            "items": [
                                {"description": "6'-0\" x 6'-8\" Sliding Glass Door", "quantity": 1, "unit": "EA"},
                            ]
                        },
                        "08 53 00 - Vinyl Windows": {
                            "items": [
                                {"description": "3'-0\" x 4'-0\" SH Vinyl Window", "quantity": 4, "unit": "EA"},
                                {"description": "2'-0\" x 3'-0\" SH Vinyl Window", "quantity": 2, "unit": "EA"},
                            ]
                        }
                    }
                },
                "12 - Furnishings": {
                    "sections": {
                        "12 32 00 - Casework": {
                            "items": [
                                {"description": "Kitchen Base Cabinet", "quantity": 10, "unit": "LF"},
                                {"description": "Kitchen Wall Cabinet", "quantity": 8, "unit": "LF"},
                                {"description": "Bathroom Vanity 30\"", "quantity": 1, "unit": "EA"},
                            ]
                        },
                        "12 36 00 - Countertops": {
                            "items": [
                                {"description": "Laminate Countertop", "quantity": 24, "unit": "SF"},
                            ]
                        }
                    }
                },
                "22 - Plumbing": {
                    "sections": {
                        "22 41 00 - Residential Fixtures": {
                            "items": [
                                {"description": "Water Closet", "quantity": 1, "unit": "EA"},
                                {"description": "Lavatory", "quantity": 1, "unit": "EA"},
                                {"description": "Bathtub/Shower Combo", "quantity": 1, "unit": "EA"},
                                {"description": "Kitchen Sink", "quantity": 1, "unit": "EA"},
                            ]
                        }
                    }
                }
            }
        }
    ]

    # Write ground truth files
    gt_dir = output_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)

    for project in sample_projects:
        gt_file = gt_dir / f"{project['project_id']}.json"
        with open(gt_file, "w") as f:
            json.dump(project, f, indent=2)
        print(f"  Created {gt_file.name}")

    # Create split files
    splits_dir = output_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    with open(splits_dir / "val.json", "w") as f:
        json.dump({"projects": ["sample_001", "sample_002", "sample_003"]}, f)

    with open(splits_dir / "test.json", "w") as f:
        json.dump({"projects": ["sample_001", "sample_002", "sample_003"]}, f)

    print(f"\nSample dataset created in {output_dir}")
    print(f"  - {len(sample_projects)} sample projects")
    print(f"  - Ground truth in {gt_dir}")


def download_cubicasa_sample(output_dir: Path) -> None:
    """Download sample images from CubiCasa5k."""
    print("\nNote: Full CubiCasa5k dataset requires separate download from:")
    print("  https://github.com/CubiCasa/CubiCasa5k")
    print("\nFor the full benchmark, you'll need to:")
    print("  1. Clone the CubiCasa5k repository")
    print("  2. Download their data files")
    print("  3. Run our annotation conversion script")


def main():
    parser = argparse.ArgumentParser(description="Download TakeoffBench dataset")
    parser.add_argument(
        "--split",
        choices=["train", "val", "test", "all"],
        default="val",
        help="Which split to download"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR,
        help="Output directory for downloaded data"
    )
    parser.add_argument(
        "--sample-only",
        action="store_true",
        help="Only create sample data (no external downloads)"
    )

    args = parser.parse_args()

    print("TakeoffBench Data Download")
    print("=" * 40)

    args.output.mkdir(parents=True, exist_ok=True)

    if args.sample_only:
        create_sample_dataset(args.output)
    else:
        create_sample_dataset(args.output)
        download_cubicasa_sample(args.output)

    print("\nDone!")


if __name__ == "__main__":
    main()
