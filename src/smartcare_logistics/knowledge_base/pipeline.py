"""
Modul Pipeline End-to-End Knowledge Base Ingestion & Indexing.
Mengorkestrasikan ekstraksi dokumen PDF, pembersihan teks, chunking,
pembuatan dense embedding, penyimpanan di ChromaDB, dan indeks BM25 leksikal.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time

from .config import (
    DOCUMENTS_DIR,
    PROCESSED_DIR,
    CHUNKS_DIR,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MAX_TOKEN_LENGTH,
)
from .pdf_extractor import PDFExtractor
from .text_cleaner import TextCleaner
from .chunker import RecursiveWordChunker
from .embedding import EmbeddingPipeline
from .vector_store import ChromaVectorStore
from .lexical_search import BM25SearchEngine


class KnowledgeBasePipeline:
    """
    Pipeline lengkap pembuatan Knowledge Base SmartCare Logistics.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.extractor = PDFExtractor(DOCUMENTS_DIR)
        self.cleaner = TextCleaner()
        self.chunker = RecursiveWordChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        # Inisialisasi lazy/on-demand untuk embedding & vector store
        self._embedding_pipeline: Optional[EmbeddingPipeline] = None
        self._vector_store: Optional[ChromaVectorStore] = None
        self._bm25_engine: Optional[BM25SearchEngine] = None

    @property
    def embedding_pipeline(self) -> EmbeddingPipeline:
        if self._embedding_pipeline is None:
            self._embedding_pipeline = EmbeddingPipeline()
        return self._embedding_pipeline

    @property
    def vector_store(self) -> ChromaVectorStore:
        if self._vector_store is None:
            self._vector_store = ChromaVectorStore()
        return self._vector_store

    @property
    def bm25_engine(self) -> BM25SearchEngine:
        if self._bm25_engine is None:
            self._bm25_engine = BM25SearchEngine()
        return self._bm25_engine

    def run_preprocessing(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Tahap 1: Ekstraksi dan Pembersihan Teks seluruh 10 dokumen PDF.
        """
        print("[1/5] Memulai ekstraksi teks dari 10 dokumen PDF resmi...")
        raw_corpus = self.extractor.extract_all_documents()

        cleaned_corpus: Dict[str, List[Dict[str, Any]]] = {}
        total_pages = 0
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        for doc_id, pages in raw_corpus.items():
            cleaned_pages = []
            for p in pages:
                clean_text = self.cleaner.clean_text(p["raw_text"])
                p_copy = dict(p)
                p_copy["clean_text"] = clean_text
                p_copy["clean_char_count"] = len(clean_text)
                cleaned_pages.append(p_copy)
                total_pages += 1
            cleaned_corpus[doc_id] = cleaned_pages

            # Simpan ringkasan ekstraksi per dokumen
            doc_summary_file = PROCESSED_DIR / f"{doc_id}_processed.json"
            with open(doc_summary_file, "w", encoding="utf-8") as f:
                json.dump(cleaned_pages, f, ensure_ascii=False, indent=2)

        print(f"[1/5] Selesai ekstraksi dan pembersihan: {len(cleaned_corpus)} dokumen, {total_pages} total halaman.")
        return cleaned_corpus

    def run_chunking(self, cleaned_corpus: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Tahap 2: Pemotongan teks secara hierarkis (Recursive Word Chunking) dan token safety check.
        """
        print(f"[2/5] Memulai chunking teks (size={self.chunk_size} kata, overlap={self.chunk_overlap} kata)...")
        all_chunks = self.chunker.chunk_corpus(cleaned_corpus)

        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
        chunks_file = CHUNKS_DIR / f"chunks_{self.chunk_size}_{self.chunk_overlap}.json"

        # Validasi token count pada setiap chunk menggunakan tokenizer
        print("[2/5] Memvalidasi batas token pada setiap chunk untuk mencegah silent truncation...")
        max_tokens_found = 0
        truncated_count = 0

        for chunk in all_chunks:
            token_count = self.embedding_pipeline.count_tokens(chunk["text"])
            chunk["metadata"]["token_count"] = token_count
            if token_count > max_tokens_found:
                max_tokens_found = token_count
            if token_count > MAX_TOKEN_LENGTH:
                truncated_count += 1

        print(f"[2/5] Total chunk dihasilkan: {len(all_chunks)}. Token maksimum: {max_tokens_found} (Batas model: {MAX_TOKEN_LENGTH}). Chunk melebihi batas: {truncated_count}.")

        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        return all_chunks

    def run_indexing(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Tahap 3 & 4: Pembuatan Dense Embeddings, Simpan ke ChromaDB, dan Bangun Indeks BM25.
        """
        print(f"[3/5] Menghasilkan dense embeddings untuk {len(chunks)} chunks dengan model E5...")
        texts = [c["text"] for c in chunks]
        t0 = time.time()
        embeddings = self.embedding_pipeline.embed_passages(texts, batch_size=32, show_progress=True)
        embed_time = time.time() - t0
        print(f"[3/5] Pembuatan embeddings selesai dalam {embed_time:.2f} detik.")

        print(f"[4/5] Menyimpan vektor ke persistent ChromaDB...")
        self.vector_store.reset()
        stored_count = self.vector_store.add_chunks(chunks, embeddings)
        print(f"[4/5] {stored_count} chunk berhasil tersimpan di ChromaDB.")

        print(f"[5/5] Membangun dan menyimpan indeks leksikal BM25...")
        self.bm25_engine.build_index(chunks)
        print(f"[5/5] Indeks BM25 berhasil dibangun.")

        return {
            "total_chunks": len(chunks),
            "stored_in_chromadb": stored_count,
            "embed_time_seconds": round(embed_time, 2),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Menjalankan seluruh alur pipeline dari korpus PDF hingga indeks siap digunakan.
        """
        t_start = time.time()
        cleaned_corpus = self.run_preprocessing()
        chunks = self.run_chunking(cleaned_corpus)
        index_stats = self.run_indexing(chunks)
        total_time = time.time() - t_start
        index_stats["total_pipeline_time_seconds"] = round(total_time, 2)
        print(f"=== PIPELINE KNOWLEDGE BASE SELESAI DALAM {total_time:.2f} DETIK ===")
        return index_stats
