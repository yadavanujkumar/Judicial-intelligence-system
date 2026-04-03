import logging
import os
import pickle
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SimilarCaseRetriever:
    """Retrieves semantically similar cases using FAISS and sentence embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "models/faiss_index"):
        self.model_name = model_name
        self.index_path = index_path
        self.index = None
        self.case_ids: List[str] = []
        self.texts: List[str] = []
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except Exception as e:
                logger.error(f"Could not load SentenceTransformer: {e}")
                self._model = None
        return self._model

    def _embed(self, texts: List[str]) -> Optional[np.ndarray]:
        model = self._get_model()
        if model is None:
            return None
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return np.array(embeddings, dtype=np.float32)

    def build_index(self, texts: List[str], case_ids: List[str]) -> bool:
        """Embed texts and build a FAISS index. Returns True on success."""
        try:
            import faiss
            embeddings = self._embed(texts)
            if embeddings is None:
                logger.warning("Embedding failed; FAISS index not built.")
                return False

            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(embeddings)
            self.case_ids = list(case_ids)
            self.texts = list(texts)
            logger.info(f"FAISS index built with {len(case_ids)} cases (dim={dim})")
            return True
        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
            return False

    def search(self, query_text: str, top_k: int = 5) -> List[dict]:
        """Return top-k similar cases for the query text."""
        if self.index is None:
            logger.warning("FAISS index not loaded; attempting to load from disk.")
            self.load_index(self.index_path)
        if self.index is None:
            return []
        try:
            query_vec = self._embed([query_text])
            if query_vec is None:
                return []
            k = min(top_k, len(self.case_ids))
            distances, indices = self.index.search(query_vec, k)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.case_ids):
                    continue
                results.append({
                    "case_id": self.case_ids[idx],
                    "similarity_score": round(float(dist), 4),
                    "text": self.texts[idx][:500] if idx < len(self.texts) else "",
                })
            return results
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []

    def save_index(self, path: str = None):
        """Persist the FAISS index and metadata to disk."""
        path = path or self.index_path
        try:
            import faiss
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            faiss.write_index(self.index, f"{path}.index")
            with open(f"{path}_meta.pkl", "wb") as f:
                pickle.dump({"case_ids": self.case_ids, "texts": self.texts}, f)
            logger.info(f"FAISS index saved to {path}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")

    def load_index(self, path: str = None):
        """Load the FAISS index and metadata from disk."""
        path = path or self.index_path
        try:
            import faiss
            index_file = f"{path}.index"
            meta_file = f"{path}_meta.pkl"
            if os.path.exists(index_file) and os.path.exists(meta_file):
                self.index = faiss.read_index(index_file)
                with open(meta_file, "rb") as f:
                    meta = pickle.load(f)
                self.case_ids = meta.get("case_ids", [])
                self.texts = meta.get("texts", [])
                logger.info(f"FAISS index loaded from {path} ({len(self.case_ids)} cases)")
            else:
                logger.warning(f"FAISS index files not found at {path}")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
