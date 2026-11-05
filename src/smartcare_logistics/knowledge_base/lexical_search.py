"""
Modul Pencarian Leksikal BM25 (Rank-BM25).
Mengindeks korpus dokumen secara leksikal untuk menangkap kecocokan kata kunci eksak,
istilah regulasi, nomor pasal, dan nama fasilitas kesehatan.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import pickle
import re
from rank_bm25 import BM25Okapi

from .config import LEXICAL_INDEX_DIR


class BM25SearchEngine:
    """
    Mesin pencari leksikal BM25Okapi dengan persistensi indeks lokal.
    """

    def __init__(self, index_dir: Optional[Path] = None):
        self.index_dir = Path(index_dir) if index_dir else LEXICAL_INDEX_DIR
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / "bm25_index.pkl"
        self.chunks_file = self.index_dir / "bm25_chunks.json"

        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[Dict[str, Any]] = []

        # Muat indeks yang sudah tersimpan jika ada
        if self.index_file.exists() and self.chunks_file.exists():
            self.load_index()

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenisasi teks untuk BM25: memisahkan kata, lowercase, mempertahankan istilah dan angka.
        """
        tokens = re.findall(r"[a-zA-Z0-9°\-]+", text.lower())
        return tokens

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Membangun indeks BM25 dari daftar chunk dokumen dan menyimpannya secara persisten.
        """
        self.chunks = chunks
        tokenized_corpus = [self.tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.save_index()

    def save_index(self) -> None:
        """
        Menyimpan model BM25 dan data chunk ke disk.
        """
        if self.bm25 is None:
            raise ValueError("Indeks BM25 belum dibangun.")

        with open(self.index_file, "wb") as f:
            pickle.dump(self.bm25, f)

        # Simpan metadata chunk
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

    def load_index(self) -> None:
        """
        Memuat model BM25 dan data chunk dari disk.
        """
        with open(self.index_file, "rb") as f:
            self.bm25 = pickle.load(f)

        with open(self.chunks_file, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian leksikal BM25 terhadap query.

        Returns:
            List of dict berisi chunk_id, text, metadata, dan bm25_score.
        """
        if self.bm25 is None or not self.chunks:
            return []

        tokenized_query = self.tokenize(query)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)
        # Urutkan index berdasarkan skor tertinggi
        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results: List[Dict[str, Any]] = []
        for idx, score in scored_indices:
            if score < 0.0:
                continue
            chunk = self.chunks[idx]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {}),
                "bm25_score": float(score),
            })

        return results
