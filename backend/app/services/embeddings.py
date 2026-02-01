from __future__ import annotations

import logging
from typing import Protocol

import numpy as np

from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> np.ndarray:
        ...

    def embed_query(self, text: str) -> np.ndarray:
        ...


class OpenAIEmbedder:
    def __init__(self, model: str, api_key: str | None):
        from langchain_openai import OpenAIEmbeddings

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
        self._embeddings = OpenAIEmbeddings(model=model, api_key=api_key)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        vectors = self._embeddings.embed_documents(texts)
        return np.array(vectors, dtype="float32")

    def embed_query(self, text: str) -> np.ndarray:
        vector = self._embeddings.embed_query(text)
        return np.array(vector, dtype="float32")


class LocalSentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            self._available = True
        except Exception as exc:
            logger.warning("SentenceTransformer not available (%s). Falling back to hash embeddings.", exc)
            self._available = False
            self._model = None

    def _hash_embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            values = [float(sum(bytearray(text.encode("utf-8")))) % 997, float(len(text) % 997)]
            vectors.append(values)
        return np.array(vectors, dtype="float32")

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if self._available and self._model:
            vectors = self._model.encode(texts, normalize_embeddings=False)
            return np.array(vectors, dtype="float32")
        return self._hash_embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        if self._available and self._model:
            vector = self._model.encode([text], normalize_embeddings=False)[0]
            return np.array(vector, dtype="float32")
        return self._hash_embed([text])[0]


def get_embedder() -> Embedder:
    settings = get_settings()
    if settings.use_local_embeddings:
        return LocalSentenceTransformerEmbedder(settings.local_embed_model)
    return OpenAIEmbedder(settings.embed_model, settings.openai_api_key)
