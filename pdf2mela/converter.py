import json
import re
import uuid
import zipfile
from pathlib import Path

from .ocr import pdf_to_recipe_async


def _strip_step_numbers(instructions: str) -> str:
    """Remove leading step numbers from each instruction line (e.g. '1.', '2)', '3 -')."""
    pattern = re.compile(r"^\s*\d+[\.\)]\s*|\s*\d+\s+-\s*")
    return "\n".join(pattern.sub("", line) for line in instructions.split("\n"))


async def _extract_recipe(pdf_path: Path, api_key: str) -> tuple[str, dict, int]:
    """Run OCR on a PDF and return (safe_filename, recipe_dict, pages_processed)."""
    raw, pages = await pdf_to_recipe_async(str(pdf_path), api_key)
    recipe_data = json.loads(raw)
    recipe_data["id"] = str(uuid.uuid4())
    recipe_data["instructions"] = _strip_step_numbers(
        recipe_data.get("instructions", "")
    )
    recipe_data["images"] = []
    filename = recipe_data["title"].replace(" ", "_").replace("/", "_")
    return filename, recipe_data, pages


async def convert(pdf_path: Path, output_dir: Path, api_key: str) -> tuple[Path, int]:
    """Convert a single PDF to a .melarecipe file and return (output_path, pages_processed)."""
    filename, recipe_data, pages = await _extract_recipe(pdf_path, api_key)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{filename}.melarecipe"

    with open(output_path, "w") as f:
        json.dump(recipe_data, f, indent=2)

    return output_path, pages


def bundle(
    recipes: list[tuple[str, dict, int]], output_dir: Path, zip_name: str = "recipes"
) -> Path:
    """Bundle pre-extracted (filename, recipe_dict) tuples into a .melarecipes ZIP file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{zip_name}.melarecipes"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, recipe_data, _ in recipes:
            zf.writestr(f"{filename}.melarecipe", json.dumps(recipe_data, indent=2))

    return output_path
