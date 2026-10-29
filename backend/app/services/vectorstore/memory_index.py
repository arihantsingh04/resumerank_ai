"""Per-request FAISS index over one resume's chunk vectors (D-04). Nothing is persisted."""

from __future__ import annotations

import faiss
import numpy as np


class MemoryIndex:
    def __init__(self, vectors: np.ndarray) -> None:
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        dim = self.vectors.shape[1] if self.vectors.ndim == 2 else 0
        self._index = faiss.IndexFlatIP(max(dim, 1))
        if len(self.vectors):
            self._index.add(self.vectors)

    def __len__(self) -> int:
        return int(self._index.ntotal)

    def search(self, queries: np.ndarray, k: int) -> list[list[tuple[int, float]]]:
        """Top-k (row position, cosine) for each query row. Vectors are L2-normalised."""
        if len(self) == 0:
            return [[] for _ in range(len(queries))]
        k = min(k, len(self))
        scores, ids = self._index.search(np.ascontiguousarray(queries, dtype=np.float32), k)
        return [
            [(int(i), float(s)) for i, s in zip(row_i, row_s, strict=True) if i != -1]
            for row_i, row_s in zip(ids, scores, strict=True)
        ]

    def mean(self) -> np.ndarray:
        """L2-normalised centroid of all vectors: the resume's overall embedding."""
        m = self.vectors.mean(axis=0)
        n = np.linalg.norm(m)
        return m / n if n > 0 else m
