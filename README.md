# pdf2mela

Convert scanned PDF recipes to [Mela](https://mela.recipes) format using Mistral OCR.

- Single PDF → `.melarecipe` (JSON)
- Multiple PDFs → `.melarecipes` (ZIP)

## Requirements

- Python 3.11+
- A [Mistral API key](https://console.mistral.ai)

## Installation

Install as tool with `uv` (recommended):

```sh
uv tool install pdf2mela
```

Or with `pip`:

```sh
pip install pdf2mela
```

Or run it directly without installing:

```sh
uvx pdf2mela --inputs recipe.pdf
```

## Usage

```sh
# Single file
pdf2mela --inputs recipe.pdf

# Multiple files
pdf2mela --inputs recipe1.pdf recipe2.pdf

# Whole directory
pdf2mela --inputs ./scans/

# Custom output directory
pdf2mela --inputs ./scans/ --output ./mela/

# Explicit API key
pdf2mela --inputs recipe.pdf --api-key YOUR_KEY
```

The Mistral API key is read from the `MISTRAL_API_KEY` environment variable by default.

## Pricing

Mistral OCR costs **$2 per 1,000 pages**. The tool prints an estimated cost at the end of each run, including what it would have cost with the 50% batch discount. See [Mistral's pricing page](https://mistral.ai/pricing#api) for up-to-date rates.

## Notes

- Recipes are extracted in their original language — no translation is applied.
- All PDFs in a run are processed concurrently.
- Failed requests are retried up to 3 times with exponential backoff.
- Set `LOGLEVEL=DEBUG` to see raw OCR responses.
