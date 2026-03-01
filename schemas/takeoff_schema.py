"""
TakeoffBench Schema Definitions

Defines the structured output format that models must produce.
Based on CSI MasterFormat for construction classification.
"""

from typing import Optional
from pydantic import BaseModel, Field


class TakeoffItem(BaseModel):
    """A single line item in the quantity takeoff."""

    description: str = Field(
        ...,
        description="Human-readable description of the item (e.g., '3-0 x 6-8 Hollow Core Door')"
    )
    quantity: float = Field(
        ...,
        ge=0,
        description="Quantity of the item"
    )
    unit: str = Field(
        ...,
        description="Unit of measure: EA (each), LF (linear feet), SF (square feet), CY (cubic yards)"
    )
    specifications: Optional[dict] = Field(
        default=None,
        description="Additional specifications (dimensions, material, finish, etc.)"
    )


class CSISection(BaseModel):
    """A CSI MasterFormat section containing items."""

    items: list[TakeoffItem] = Field(
        default_factory=list,
        description="List of takeoff items in this section"
    )


class CSIDivision(BaseModel):
    """A CSI MasterFormat division containing sections."""

    sections: dict[str, CSISection] = Field(
        default_factory=dict,
        description="Mapping of section codes to sections (e.g., '08 14 16' -> Wood Doors)"
    )


class TakeoffSchedule(BaseModel):
    """Complete quantity takeoff schedule for a drawing."""

    project_id: str = Field(
        ...,
        description="Unique identifier for the project/drawing"
    )
    drawing_sheets: list[str] = Field(
        default_factory=list,
        description="List of drawing sheet IDs used for this takeoff"
    )
    divisions: dict[str, CSIDivision] = Field(
        default_factory=dict,
        description="Mapping of division names to divisions (e.g., '08 - Openings')"
    )

    def to_flat_items(self) -> list[dict]:
        """Flatten the schedule to a list of items with full paths."""
        items = []
        for div_name, division in self.divisions.items():
            for section_code, section in division.sections.items():
                for item in section.items:
                    items.append({
                        "division": div_name,
                        "section": section_code,
                        "description": item.description,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "specifications": item.specifications
                    })
        return items


# CSI MasterFormat Division Reference (commonly used in takeoffs)
CSI_DIVISIONS = {
    "03": "Concrete",
    "04": "Masonry",
    "05": "Metals",
    "06": "Wood, Plastics, and Composites",
    "07": "Thermal and Moisture Protection",
    "08": "Openings",
    "09": "Finishes",
    "10": "Specialties",
    "11": "Equipment",
    "12": "Furnishings",
    "22": "Plumbing",
    "23": "HVAC",
    "26": "Electrical",
}

# Common section codes for residential/commercial takeoffs
CSI_SECTIONS = {
    # Division 08 - Openings
    "08 11 13": "Hollow Metal Doors and Frames",
    "08 11 16": "Aluminum Doors and Frames",
    "08 14 16": "Flush Wood Doors",
    "08 14 33": "Stile and Rail Wood Doors",
    "08 32 13": "Sliding Aluminum-Framed Glass Doors",
    "08 41 13": "Aluminum-Framed Entrances",
    "08 51 13": "Aluminum Windows",
    "08 52 00": "Wood Windows",
    "08 53 00": "Vinyl Windows",
    "08 71 00": "Door Hardware",

    # Division 09 - Finishes
    "09 21 16": "Gypsum Board Assemblies",
    "09 29 00": "Gypsum Board",
    "09 30 00": "Tiling",
    "09 51 00": "Acoustical Ceilings",
    "09 65 00": "Resilient Flooring",
    "09 68 00": "Carpeting",
    "09 91 00": "Painting",

    # Division 12 - Furnishings
    "12 32 00": "Manufactured Wood Casework",
    "12 35 00": "Specialty Casework",
    "12 36 00": "Countertops",

    # Division 22 - Plumbing
    "22 40 00": "Plumbing Fixtures",
    "22 41 00": "Residential Plumbing Fixtures",
    "22 42 00": "Commercial Plumbing Fixtures",

    # Division 26 - Electrical
    "26 27 26": "Wiring Devices",
    "26 51 00": "Interior Lighting",
    "26 56 00": "Exterior Lighting",
}


# Element type taxonomy for detection/classification
ELEMENT_TYPES = {
    "doors": {
        "interior_door": ["swing", "pocket", "sliding", "bifold"],
        "exterior_door": ["entry", "patio", "garage"],
    },
    "windows": {
        "window": ["single_hung", "double_hung", "casement", "sliding", "fixed"],
    },
    "fixtures": {
        "plumbing_fixture": ["toilet", "sink", "bathtub", "shower", "urinal"],
        "kitchen_fixture": ["sink", "dishwasher", "range", "refrigerator"],
    },
    "finishes": {
        "flooring": ["tile", "carpet", "hardwood", "vinyl", "concrete"],
        "wall_finish": ["paint", "wallpaper", "tile", "paneling"],
        "ceiling": ["drywall", "acoustic_tile", "exposed"],
    },
    "casework": {
        "cabinet": ["base", "wall", "tall", "vanity"],
        "countertop": ["laminate", "granite", "quartz", "solid_surface"],
    },
}


def validate_takeoff(takeoff: dict) -> tuple[bool, list[str]]:
    """Validate a takeoff dictionary against the schema."""
    errors = []

    try:
        TakeoffSchedule(**takeoff)
        return True, []
    except Exception as e:
        errors.append(str(e))
        return False, errors


if __name__ == "__main__":
    # Example usage
    example = TakeoffSchedule(
        project_id="residential_001",
        drawing_sheets=["A-101"],
        divisions={
            "08 - Openings": CSIDivision(
                sections={
                    "08 14 16": CSISection(
                        items=[
                            TakeoffItem(
                                description="3'-0\" x 6'-8\" Hollow Core Door",
                                quantity=6,
                                unit="EA",
                                specifications={"material": "wood", "finish": "paint_grade"}
                            )
                        ]
                    )
                }
            )
        }
    )

    print("Example takeoff schedule:")
    print(example.model_dump_json(indent=2))
