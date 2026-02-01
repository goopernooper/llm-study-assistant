from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Tuple

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FaissIndex:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.index: faiss.IndexIDMap2 | None = None
        self._load()

    def _load(self) -> None:
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                logger.info("Loaded FAISS index from %s", self.index_path)
            except Exception as exc:
                logger.warning("Failed to load FAISS index (%s). Recreating.", exc)
                self.index = None

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            base = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIDMap2(base)

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        vectors = vectors.astype("float32")
        faiss.normalize_L2(vectors)
        return vectors

    def add_embeddings(self, embeddings: np.ndarray, ids: Iterable[int]) -> None:
        if embeddings.size == 0:
            return
        embeddings = np.atleast_2d(embeddings)
        ids_array = np.array(list(ids), dtype="int64")
        self._ensure_index(embeddings.shape[1])
        vectors = self._normalize(embeddings)
        self.index.add_with_ids(vectors, ids_array)
        self.persist()

    def search(self, query_vector: np.ndarray, top_k: int) -> List[Tuple[int, float]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        query_vector = np.atleast_2d(query_vector)
        query_vector = self._normalize(query_vector)
        scores, ids = self.index.search(query_vector, top_k)
        results: List[Tuple[int, float]] = []
        for idx, score in zip(ids[0], scores[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))
        return results

    def delete(self, ids: Iterable[int]) -> None:
        if self.index is None:
            return
        ids_array = np.array(list(ids), dtype="int64")
        if ids_array.size == 0:
            return
        self.index.remove_ids(ids_array)
        self.persist()

    def persist(self) -> None:
        if self.index is None:
            return
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))

    def count(self) -> int:
        if self.index is None:
            return 0
        return int(self.index.ntotal)
