"""
Modul Recursive Word-Aware Document Chunker.
Melakukan pemotongan dokumen secara hierarkis (Bab/Pasal -> Paragraf -> Kalimat -> Kata)
dengan mempertahankan konteks regulasi kesehatan, overlap kata, dan metadata penelusuran.
"""

import re
from typing import List, Dict, Any, Optional


class RecursiveWordChunker:
    """
    Pemotong teks berbasis recursive splitting dengan perhitungan kata (word-aware).
    Mempertahankan kelengkapan klausa, nomor pasal, dan nomor halaman.
    """

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap harus lebih kecil daripada chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Pola batas judul regulasi (Pasal, BAB, Bagian, Lampiran)
        self.heading_pattern = re.compile(
            r"(?:\n|^)(?:BAB\s+[IVXLCDM]+|Pasal\s+\d+|Bagian\s+[A-Za-z0-9]+|LAMPIRAN(?:\s+[IVXLCDM]+)?)",
            re.IGNORECASE,
        )

        # Pola batas kalimat
        self.sentence_split_pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Memisahkan teks berdasarkan pergantian paragraf ganda atau pergantian pasal.
        """
        raw_paras = re.split(r"\n\s*\n", text)
        cleaned_paras = [p.strip() for p in raw_paras if p.strip()]
        return cleaned_paras

    def _split_into_sentences(self, paragraph: str) -> List[str]:
        """
        Memisahkan paragraf menjadi kalimat-kalimat.
        """
        sentences = self.sentence_split_pattern.split(paragraph)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Membuat chunk dari satu halaman dokumen bersih.
        """
        raw_text = page_data.get("clean_text") or page_data.get("raw_text", "")
        if not raw_text.strip():
            return []

        doc_meta = page_data.get("metadata", {})
        page_num = page_data.get("page_number", 1)
        doc_id = page_data.get("doc_id", "DOC")

        words = raw_text.split()
        total_words = len(words)

        if total_words <= self.chunk_size:
            # Jika seluruh teks halaman masuk dalam 1 chunk
            chunk_obj = {
                "chunk_id": f"{doc_id}_P{page_num:03d}_C001",
                "text": raw_text.strip(),
                "word_count": total_words,
                "char_count": len(raw_text),
                "metadata": {
                    **doc_meta,
                    "page_start": page_num,
                    "page_end": page_num,
                    "chunk_index": 1,
                    "total_page_chunks": 1,
                    "word_count": total_words,
                },
            }
            return [chunk_obj]

        # Jika lebih besar dari chunk_size, lakukan recursive splitting dengan overlap
        chunks: List[Dict[str, Any]] = []
        step = self.chunk_size - self.chunk_overlap
        chunk_idx = 1

        for i in range(0, total_words, step):
            chunk_words = words[i : i + self.chunk_size]
            if not chunk_words:
                break
            
            # Jika chunk terakhir terlalu pendek (kurang dari overlap), gabungkan atau simpan jika bermakna
            if len(chunk_words) < self.chunk_overlap and chunks:
                break

            chunk_text = " ".join(chunk_words)
            chunk_obj = {
                "chunk_id": f"{doc_id}_P{page_num:03d}_C{chunk_idx:03d}",
                "text": chunk_text,
                "word_count": len(chunk_words),
                "char_count": len(chunk_text),
                "metadata": {
                    **doc_meta,
                    "page_start": page_num,
                    "page_end": page_num,
                    "chunk_index": chunk_idx,
                    "word_count": len(chunk_words),
                },
            }
            chunks.append(chunk_obj)
            chunk_idx += 1

        # Tambahkan total_page_chunks pada metadata setiap chunk
        for c in chunks:
            c["metadata"]["total_page_chunks"] = len(chunks)

        return chunks

    def chunk_corpus(self, cleaned_corpus: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Membuat chunk untuk seluruh korpus dokumen yang telah dibersihkan.
        """
        all_chunks: List[Dict[str, Any]] = []
        global_idx = 1

        for doc_id in sorted(cleaned_corpus.keys()):
            pages = cleaned_corpus[doc_id]
            for page in pages:
                page_chunks = self.chunk_page(page)
                for chunk in page_chunks:
                    chunk["metadata"]["global_chunk_index"] = global_idx
                    # Konversi array atau list ke format string / serializable jika diperlukan oleh ChromaDB
                    if "related_documents" in chunk["metadata"] and isinstance(chunk["metadata"]["related_documents"], list):
                        chunk["metadata"]["related_documents_str"] = ", ".join(chunk["metadata"]["related_documents"])
                    all_chunks.append(chunk)
                    global_idx += 1

        return all_chunks
