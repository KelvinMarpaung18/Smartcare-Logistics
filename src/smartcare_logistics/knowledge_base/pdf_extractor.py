"""
Modul Ekstraksi Dokumen PDF menggunakan PyMuPDF (fitz).
Mengekstrak teks halaman per halaman secara terstruktur dengan pelacakan nomor halaman asli.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pymupdf

from .document_metadata import OFFICIAL_DOCUMENTS_REGISTRY, get_document_metadata


class PDFExtractor:
    """
    Ekstraktor teks dokumen PDF berbasis PyMuPDF.
    Mempertahankan nomor halaman fisik dokumen dan struktur teks per halaman.
    """

    def __init__(self, documents_dir: Path):
        self.documents_dir = Path(documents_dir)

    def extract_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Mengekstrak seluruh halaman dari dokumen yang ditentukan oleh doc_id.
        Menerapkan filter halaman khusus jika terdefinisi di metadata (misal DOC06).

        Returns:
            List of dict berisi:
                - doc_id: ID dokumen (misal 'DOC01')
                - page_num: Nomor halaman PDF fisik (1-based)
                - raw_text: Teks mentah hasil ekstraksi
                - metadata: Metadata resmi dokumen
        """
        meta = get_document_metadata(doc_id)
        if not meta:
            raise ValueError(f"Metadata untuk dokumen '{doc_id}' tidak ditemukan dalam registri resmi.")

        file_path = self.documents_dir / meta["file_name"]
        if not file_path.exists():
            raise FileNotFoundError(f"File PDF tidak ditemukan: {file_path}")

        extracted_pages: List[Dict[str, Any]] = []
        page_filter = meta.get("page_filter")  # misal (108, 150) untuk DOC06

        doc = pymupdf.open(str(file_path))
        try:
            total_pages = len(doc)
            for idx in range(total_pages):
                page_num = idx + 1  # 1-based indexing

                # Terapkan filter halaman jika didefinisikan
                if page_filter is not None:
                    start_page, end_page = page_filter
                    if not (start_page <= page_num <= end_page):
                        continue

                page = doc[idx]
                text = page.get_text("text")

                # Simpan metadata per halaman
                page_data = {
                    "doc_id": doc_id,
                    "file_name": meta["file_name"],
                    "page_number": page_num,
                    "total_pdf_pages": total_pages,
                    "raw_text": text,
                    "metadata": {
                        "document_id": meta["document_id"],
                        "title": meta["title"],
                        "publisher": meta["publisher"],
                        "publication_year": meta["publication_year"],
                        "document_type": meta["document_type"],
                        "category": meta["category"],
                        "source": meta["file_name"],
                        "file_name": meta["file_name"],
                        "page_number": page_num,
                        "related_documents": meta.get("related_documents", []),
                    },
                }
                extracted_pages.append(page_data)
        finally:
            doc.close()

        return extracted_pages

    def extract_all_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Mengekstrak seluruh 10 dokumen resmi yang terdaftar.
        """
        all_corpus: Dict[str, List[Dict[str, Any]]] = {}
        for doc_id in sorted(OFFICIAL_DOCUMENTS_REGISTRY.keys()):
            pages = self.extract_document(doc_id)
            all_corpus[doc_id] = pages
        return all_corpus
