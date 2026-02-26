import base64

from loguru import logger
from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import MelaRecipe

ANNOTATION_PROMPT = (
    "Extract the recipe from the document and fill in the fields. "
    "Preserve the original language of the document exactly — do not translate any text. "
    "This includes all fields such as yield, prepTime, cookTime, and totalTime: "
    "use the exact wording from the document, or if these fields are not explicitly stated, "
    "express them in the same language as the rest of the recipe. "
    "Do not extract or encode any images — always leave the images field as an empty list."
)


def _make_retry_logger(pdf_path: str):
    def log(retry_state):
        logger.warning(
            "Retrying {} (attempt {})...",
            pdf_path,
            retry_state.attempt_number,
        )

    return log


async def pdf_to_recipe_async(pdf_path: str, api_key: str) -> tuple[str, int]:
    """Read a PDF file and extract a structured recipe using Mistral OCR (async).

    Returns a tuple of (annotation_json, pages_processed).
    """
    with open(pdf_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

    client = Mistral(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=_make_retry_logger(pdf_path),
        reraise=True,
    )
    async def _call() -> tuple[str, int]:
        response = await client.ocr.process_async(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}",
            },
            document_annotation_format=response_format_from_pydantic_model(MelaRecipe),
            document_annotation_prompt=ANNOTATION_PROMPT,
        )
        raw = response.document_annotation
        if not raw:
            raise ValueError("OCR returned empty annotation")
        pages = response.usage_info.pages_processed
        logger.debug("Raw OCR response for {} ({} page(s)):\n{}", pdf_path, pages, raw)
        return raw, pages

    return await _call()
