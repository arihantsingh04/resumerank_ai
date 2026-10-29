"""Text → vector encoders (D-03, D-19)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Protocol

import numpy as np

log = logging.getLogger(__name__)


class Encoder(Protocol):
    @property
    def dim(self) -> int: ...

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return float32 array (len(texts), dim), each row L2-normalised."""
        ...


class LazySentenceTransformerEncoder:
    """Loads the Sentence-Transformers model on first use, once per process, on CPU."""

    def __init__(self, model_name: str, cache_dir: Path, batch_size: int = 32) -> None:
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    log.info("loading embedding model %s", self.model_name)
                    self._model = SentenceTransformer(
                        self.model_name, device="cpu", cache_folder=str(self.cache_dir)
                    )
        return self._model

    def warmup(self) -> None:
        self._load()

    @property
    def dim(self) -> int:
        return int(self._load().get_sentence_embedding_dimension())

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        vecs = self._load().encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float32)


class LazyOnnxEncoder:
    """The same Sentence-Transformers model run through ONNX Runtime instead of PyTorch (D-46).

    Downloads the model's official ONNX export + tokenizer from the Hugging Face repo on first use, then
    reproduces the sentence-transformers pipeline exactly: tokenize (max 256 tokens), run the transformer,
    mean-pool over the attention mask, L2-normalise. ~60 MB of dependencies instead of ~700 MB for PyTorch,
    which is what lets the API fit in a serverless function.
    """

    MAX_TOKENS = 256

    def __init__(self, model_name: str, cache_dir: Path, batch_size: int = 32) -> None:
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self._session = None
        self._tokenizer = None
        self._lock = threading.Lock()

    def _load(self):
        if self._session is None:
            with self._lock:
                if self._session is None:
                    import onnxruntime as ort
                    from huggingface_hub import hf_hub_download
                    from tokenizers import Tokenizer

                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    log.info("loading ONNX embedding model %s", self.model_name)
                    kw = {"repo_id": self.model_name, "cache_dir": str(self.cache_dir)}
                    tok = Tokenizer.from_file(hf_hub_download(filename="tokenizer.json", **kw))
                    tok.enable_truncation(max_length=self.MAX_TOKENS)
                    tok.enable_padding(pad_id=0, pad_token="[PAD]")  # noqa: S106 (tokenizer padding token)
                    opts = ort.SessionOptions()
                    opts.intra_op_num_threads = 2  # predictable CPU use on small servers / laptops
                    self._session = ort.InferenceSession(
                        hf_hub_download(filename="onnx/model.onnx", **kw),
                        sess_options=opts,
                        providers=["CPUExecutionProvider"],
                    )
                    self._tokenizer = tok
        return self._session

    def warmup(self) -> None:
        self._load()

    @property
    def dim(self) -> int:
        return 384 if "MiniLM-L6" in self.model_name else int(self.encode(["dim"]).shape[1])

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        session = self._load()
        input_names = {i.name for i in session.get_inputs()}
        out = []
        for start in range(0, len(texts), self.batch_size):
            batch = self._tokenizer.encode_batch(texts[start : start + self.batch_size])
            ids = np.array([e.ids for e in batch], dtype=np.int64)
            mask = np.array([e.attention_mask for e in batch], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in input_names:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = session.run(None, feeds)[0]  # (batch, tokens, dim)
            m = mask[..., None].astype(np.float32)
            pooled = (hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
            pooled /= np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)
            out.append(pooled.astype(np.float32))
        return np.vstack(out)


def build_encoder(settings) -> Encoder:
    """Pick the embedding backend. "auto" uses PyTorch Sentence-Transformers when installed (local laptop),
    otherwise ONNX Runtime (serverless deploys, where PyTorch is too big)."""
    backend = settings.embedding_backend
    if backend == "auto":
        try:
            import sentence_transformers  # noqa: F401
        except ImportError:
            backend = "onnx"
        else:
            backend = "torch"
    cls = LazySentenceTransformerEncoder if backend == "torch" else LazyOnnxEncoder
    return cls(settings.embedding_model, settings.models_dir)
