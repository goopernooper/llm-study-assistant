from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PageText:
    page_number: int
    text: str


def _clean_repeated_lines(pages: List[PageText]) -> List[PageText]:
    if not pages:
        return pages

    header_counts: dict[str, int] = {}
    footer_counts: dict[str, int] = {}

    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        if not lines:
            continue
        header = "\n".join(lines[:2])
        footer = "\n".join(lines[-2:])
        if header:
            header_counts[header] = header_counts.get(header, 0) + 1
        if footer:
            footer_counts[footer] = footer_counts.get(footer, 0) + 1

    threshold = max(2, int(len(pages) * 0.6))
    repeated_headers = {h for h, c in header_counts.items() if c >= threshold}
    repeated_footers = {f for f, c in footer_counts.items() if c >= threshold}

    cleaned_pages: List[PageText] = []
    for page in pages:
        lines = [line for line in page.text.splitlines()]
        stripped_lines = [line.strip() for line in lines if line.strip()]
        if not stripped_lines:
            cleaned_pages.append(page)
            continue
        header = "\n".join(stripped_lines[:2])
        footer = "\n".join(stripped_lines[-2:])

        new_lines = lines[:]
        if header in repeated_headers:
            new_lines = new_lines[2:]
        if footer in repeated_footers and len(new_lines) >= 2:
            new_lines = new_lines[:-2]
        cleaned_pages.append(PageText(page.page_number, "\n".join(new_lines).strip()))

    return cleaned_pages


def extract_text_pages(path: str) -> List[PageText]:
    pages: List[PageText] = []
    try:
        import fitz  # PyMuPDF

        with fitz.open(path) as doc:
            for index, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                pages.append(PageText(page_number=index, text=text))
    except Exception:
        try:
            import pdfplumber

            with pdfplumber.open(path) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    pages.append(PageText(page_number=index, text=text))
        except Exception as exc:
            raise RuntimeError("Failed to extract PDF text with PyMuPDF or pdfplumber") from exc

    return _clean_repeated_lines(pages)
