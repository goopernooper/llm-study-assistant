from __future__ import annotations

from langchain_text_splitters import TokenTextSplitter


_splitter = TokenTextSplitter(chunk_size=800, chunk_overlap=120, encoding_name="cl100k_base")


def chunk_text(text: str) -> list[str]:
    if not text:
        return []
    return [chunk.strip() for chunk in _splitter.split_text(text) if chunk.strip()]
