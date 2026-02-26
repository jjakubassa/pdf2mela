import asyncio
import json
import os
import sys
from pathlib import Path

import tyro
from loguru import logger

from .converter import _extract_recipe, bundle


def collect_pdfs(inputs: list[Path]) -> list[Path]:
    """Expand directories to PDF files and validate all paths exist."""
    pdfs: list[Path] = []
    for path in inputs:
        if not path.exists():
            logger.error("Path does not exist: {}", path)
            sys.exit(1)
        if path.is_dir():
            found = sorted(path.glob("*.pdf"))
            if not found:
                logger.warning("No PDF files found in directory: {}", path)
            pdfs.extend(found)
        elif path.suffix.lower() == ".pdf":
            pdfs.append(path)
        else:
            logger.error("Not a PDF file: {}", path)
            sys.exit(1)
    return pdfs


# Mistral OCR pricing: $2 per 1,000 pages (50% off for batch jobs)
OCR_COST_PER_PAGE = 2.0 / 1000.0
OCR_COST_PER_PAGE_BATCH = OCR_COST_PER_PAGE * 0.5


async def process_pdf(
    pdf: Path, output: Path, api_key: str
) -> tuple[str, dict, int] | None:
    """Run OCR on a single PDF and return the extracted recipe, or None on failure."""
    try:
        result = await _extract_recipe(pdf, api_key)
        logger.info("Processing {} ... done ({} page(s))", pdf.name, result[2])
        return result
    except Exception as e:
        logger.error("Processing {} ... failed: {}", pdf.name, e)
        return None


async def run(inputs: list[Path], output: Path, api_key: str) -> None:
    pdfs = collect_pdfs(inputs)
    if not pdfs:
        logger.error("No PDF files to process.")
        sys.exit(1)

    logger.info("Converting {} file(s) → {}/", len(pdfs), output)

    tasks = [process_pdf(pdf, output, api_key) for pdf in pdfs]
    results = await asyncio.gather(*tasks)
    recipes = [r for r in results if r is not None]
    failed = len(results) - len(recipes)
    total_pages = sum(r[2] for r in recipes)

    if not recipes:
        logger.error("All files failed to convert.")
        sys.exit(1)

    if len(pdfs) == 1:
        filename, recipe_data, _ = recipes[0]
        output.mkdir(parents=True, exist_ok=True)
        output_path = output / f"{filename}.melarecipe"
        with open(output_path, "w") as f:
            json.dump(recipe_data, f, indent=2)
        logger.info("Saved → {}", output_path.name)
    else:
        try:
            output_path = bundle(recipes, output)
            logger.info(
                "Bundling {} recipe(s) ... done → {}", len(recipes), output_path.name
            )
        except Exception as e:
            logger.error("Bundling {} recipe(s) ... failed: {}", len(recipes), e)

    if failed:
        logger.warning("{} file(s) failed to convert.", failed)

    estimated_cost = total_pages * OCR_COST_PER_PAGE
    estimated_cost_batch = total_pages * OCR_COST_PER_PAGE_BATCH
    logger.info(
        "Total pages processed: {} — estimated cost: ${:.4f} (${:.4f} with batch)",
        total_pages,
        estimated_cost,
        estimated_cost_batch,
    )


def main(
    inputs: list[Path],
    output: Path = Path("data/output"),
    api_key: str = "",
) -> None:
    """Convert PDF recipe files to .melarecipe format.

    Args:
        inputs: One or more PDF files or directories containing PDF files.
        output: Directory to write the output file(s) to.
        api_key: Mistral API key (defaults to $MISTRAL_API_KEY).
    """
    if not api_key:
        api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        logger.error("Mistral API key not set. Pass --api-key or set $MISTRAL_API_KEY.")
        sys.exit(1)

    asyncio.run(run(inputs, output, api_key))


def cli() -> None:
    log_level = os.environ.get("LOGLEVEL", "INFO").upper()
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    tyro.cli(main)


if __name__ == "__main__":
    cli()
