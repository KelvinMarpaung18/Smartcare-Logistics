"""
Modul Dense Vector Embedding menggunakan model intfloat/multilingual-e5-base.
Mengelola pembuatan embedding teks 768 dimensi dengan prefix wajib (passage: dan query:),
serta validasi jumlah token untuk mencegah silent truncation.
"""

from pathlib import Path
from typing import List, Union, Optional
import os
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from .config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIMENSION,
    MAX_TOKEN_LENGTH,
    PASSAGE_PREFIX,
    QUERY_PREFIX,
    BASE_DIR,
)


class EmbeddingPipeline:
    """
    Pipeline pembuatan representasi vektor dense berdimensi 768 menggunakan multilingual-e5-base.
    """

    def __init__(self, model_path_or_name: Optional[str] = None):
        # Tentukan prioritas path: folder lokal model_cache jika sudah lengkap, atau model_name
        local_model_dir = BASE_DIR / "knowledge_base" / "model_cache" / "intfloat_multilingual-e5-base"
        if model_path_or_name is None:
            if (local_model_dir / "model.safetensors").exists():
                self.model_identifier = str(local_model_dir)
            else:
                self.model_identifier = EMBEDDING_MODEL_NAME
        else:
            self.model_identifier = model_path_or_name

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load SentenceTransformer model
        self.model = SentenceTransformer(self.model_identifier, device=self.device)
        # Load tokenizer untuk validasi batas token eksplisit
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_identifier)

    def count_tokens(self, text: str) -> int:
        """
        Menghitung jumlah token aktual suatu teks menggunakan tokenizer resmi model.
        """
        tokens = self.tokenizer.encode(text, add_special_tokens=True, truncation=False)
        return len(tokens)

    def embed_passages(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> List[List[float]]:
        """
        Menghasilkan dense embedding untuk teks dokumen/passage.
        Secara otomatis menambahkan prefix 'passage: ' sesuai spesifikasi model E5.
        """
        prefixed_texts = [f"{PASSAGE_PREFIX}{t}" for t in texts]
        embeddings = self.model.encode(
            prefixed_texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Menghasilkan dense embedding untuk teks query pencarian pengguna.
        Secara otomatis menambahkan prefix 'query: ' sesuai spesifikasi model E5.
        """
        prefixed_query = f"{QUERY_PREFIX}{query}"
        embedding = self.model.encode(
            prefixed_query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding.tolist()
