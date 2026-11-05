"""
Modul Manajemen Persistent ChromaDB Vector Store.
Menyimpan dan mengelola indeks vektor dense dengan metrik jarak kosinus (cosine distance),
serta mendukung metadata filtering dan idempotent insertion.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from .config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME


class ChromaVectorStore:
    """
    Wrapper ChromaDB persistent untuk koleksi pengetahuan logistik kesehatan.
    """

    def __init__(self, persist_directory: Optional[Path] = None):
        self.persist_dir = Path(persist_directory) if persist_directory else CHROMA_DB_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Inisialisasi ChromaDB client persisten
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False, is_persistent=True),
        )

        # Buat atau ambil koleksi dengan konfigurasi ruang vektor jarak kosinus
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _sanitize_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Membersihkan metadata agar kompatibel dengan ChromaDB (hanya str, int, float, bool).
        """
        clean_meta = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                clean_meta[k] = ", ".join(str(item) for item in v)
            elif v is None:
                clean_meta[k] = ""
            else:
                clean_meta[k] = str(v)
        return clean_meta

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        batch_size: int = 100,
    ) -> int:
        """
        Menyimpan potongan teks (chunks) dan vektor embeddings ke ChromaDB secara idempotent.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Jumlah chunk dan embeddings harus sama.")

        total = len(chunks)
        for i in range(0, total, batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]

            ids = [c["chunk_id"] for c in batch_chunks]
            documents = [c["text"] for c in batch_chunks]
            metadatas = [self._sanitize_metadata(c.get("metadata", {})) for c in batch_chunks]

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas,
            )

        return total

    def query_similarity(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian kemiripan semantik dense vector.

        Returns:
            List of dict berisi:
                - chunk_id: ID chunk
                - text: Teks isi chunk
                - metadata: Metadata chunk
                - distance: Cosine distance (0.0 identik, makin besar makin beda)
                - similarity: 1 - distance (1.0 identik, makin tinggi makin relevan)
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return formatted_results

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists):
            # Dalam ChromaDB hnsw:space cosine, distance adalah cosine distance
            # Similarity = 1.0 - distance
            similarity = max(0.0, 1.0 - dist)
            formatted_results.append({
                "chunk_id": chunk_id,
                "text": doc,
                "metadata": meta,
                "distance": float(dist),
                "similarity": float(similarity),
            })

        return formatted_results

    def count(self) -> int:
        """
        Mengembalikan jumlah chunk yang tersimpan di dalam koleksi.
        """
        return self.collection.count()

    def reset(self) -> None:
        """
        Mengosongkan dan membuat ulang koleksi.
        """
        self.client.delete_collection(CHROMA_COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
