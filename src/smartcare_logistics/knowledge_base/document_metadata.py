"""
Registri metadata resmi untuk 10 korpus dokumen logistik kesehatan SmartCare Logistics.
Menjamin keterlacakan (traceability) dan integritas metadata setiap sumber dokumen.
"""

from typing import Dict, Any, Optional

OFFICIAL_DOCUMENTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "DOC01": {
        "document_id": "DOC01",
        "file_name": "DOC01_Permenkes_74_2016.pdf",
        "title": "Peraturan Menteri Kesehatan Republik Indonesia Nomor 74 Tahun 2016 tentang Standar Pelayanan Kefarmasian di Puskesmas",
        "short_title": "Standar Pelayanan Kefarmasian di Puskesmas",
        "publisher": "Kementerian Kesehatan Republik Indonesia",
        "publication_year": 2016,
        "document_type": "Peraturan Perundang-undangan (Permenkes)",
        "category": "Pharmaceutical Management & Healthcare Facility",
        "description": "Pedoman tata kelola pengelolaan sediaan farmasi dan bahan medis habis pakai (BMHP) serta pelayanan farmasi klinis di Puskesmas.",
        "related_documents": [],
        "page_filter": None,  # Proses seluruh halaman
    },
    "DOC02": {
        "document_id": "DOC02",
        "file_name": "DOC02_Permenkes_26_2020.pdf",
        "title": "Peraturan Menteri Kesehatan Republik Indonesia Nomor 26 Tahun 2020 tentang Perubahan atas Permenkes Nomor 74 Tahun 2016 tentang Standar Pelayanan Kefarmasian di Puskesmas",
        "short_title": "Perubahan Standar Pelayanan Kefarmasian di Puskesmas",
        "publisher": "Kementerian Kesehatan Republik Indonesia",
        "publication_year": 2020,
        "document_type": "Peraturan Perundang-undangan (Permenkes)",
        "category": "Policy and Regulation",
        "description": "Amandemen dan penyesuaian ketentuan operasional kefarmasian serta tata laksana pelaporan pada Puskesmas.",
        "related_documents": ["DOC01_Permenkes_74_2016.pdf"],
        "page_filter": None,
    },
    "DOC03": {
        "document_id": "DOC03",
        "file_name": "DOC03_Permenkes_72_2016.pdf",
        "title": "Peraturan Menteri Kesehatan Republik Indonesia Nomor 72 Tahun 2016 tentang Standar Pelayanan Kefarmasian di Rumah Sakit",
        "short_title": "Standar Pelayanan Kefarmasian di Rumah Sakit",
        "publisher": "Kementerian Kesehatan Republik Indonesia",
        "publication_year": 2016,
        "document_type": "Peraturan Perundang-undangan (Permenkes)",
        "category": "Pharmaceutical Management & Healthcare Facility",
        "description": "Standar pengelolaan perbekalan farmasi, sistem distribusi unit dose, penyimpanan khusus, dan pelayanan farmasi rumah sakit.",
        "related_documents": [],
        "page_filter": None,
    },
    "DOC04": {
        "document_id": "DOC04",
        "file_name": "DOC04_Permenkes_73_2016.pdf",
        "title": "Peraturan Menteri Kesehatan Republik Indonesia Nomor 73 Tahun 2016 tentang Standar Pelayanan Kefarmasian di Apotek",
        "short_title": "Standar Pelayanan Kefarmasian di Apotek",
        "publisher": "Kementerian Kesehatan Republik Indonesia",
        "publication_year": 2016,
        "document_type": "Peraturan Perundang-undangan (Permenkes)",
        "category": "Pharmaceutical Management",
        "description": "Standar operasional pengelolaan obat, penyimpanan, penyerahan, dan dispensing perbekalan farmasi di apotek.",
        "related_documents": [],
        "page_filter": None,
    },
    "DOC05": {
        "document_id": "DOC05",
        "file_name": "DOC05_Permenkes_19_2024.pdf",
        "title": "Peraturan Menteri Kesehatan Republik Indonesia Nomor 19 Tahun 2024 tentang Penyelenggaraan Pusat Kesehatan Masyarakat",
        "short_title": "Penyelenggaraan Puskesmas",
        "publisher": "Kementerian Kesehatan Republik Indonesia",
        "publication_year": 2024,
        "document_type": "Peraturan Perundang-undangan (Permenkes)",
        "category": "Healthcare Facility & Policy",
        "description": "Regulasi terkini mengenai tata kelola, klasifikasi, sarana prasarana, logistik pendukung, dan operasional layanan Puskesmas.",
        "related_documents": [],
        "page_filter": None,
    },
    "DOC06": {
        "document_id": "DOC06",
        "file_name": "DOC06_Modul_Pelatihan_Imunisasi.pdf",
        "title": "Modul Pelatihan Pengelola Imunisasi Puskesmas - Modul 4: Pengelolaan Rantai Dingin Vaksin, Vaksin dan Logistik Imunisasi",
        "short_title": "Modul Pelatihan Rantai Dingin Vaksin Puskesmas",
        "publisher": "Direktorat Pengelolaan Imunisasi, Kementerian Kesehatan RI",
        "publication_year": 2024,
        "document_type": "Modul Pelatihan Teknis",
        "category": "Vaccine Management & Cold Chain",
        "description": "Petunjuk teknis operasional pengelolaan rantai dingin, pemeliharaan suhu 2C hingga 8C, tata cara pengepakan vaksin carrier, dan pemantauan suhu logistik imunisasi di Puskesmas.",
        "related_documents": [],
        # Wajib fokus pada Modul 4 di halaman PDF 108–150 (halaman internal 96–136)
        "page_filter": (108, 150),
    },
    "DOC07": {
        "document_id": "DOC07",
        "file_name": "DOC07_RAK_Imunisasi_2025_2029.pdf",
        "title": "Rencana Aksi Kegiatan Direktorat Pengelolaan Imunisasi Tahun 2025-2029",
        "short_title": "Rencana Aksi Direktorat Imunisasi 2025-2029",
        "publisher": "Direktorat Pengelolaan Imunisasi, Kementerian Kesehatan RI",
        "publication_year": 2024,
        "document_type": "Dokumen Kebijakan dan Perencanaan Strategis",
        "category": "Policy and Regulation",
        "description": "Dokumen perencanaan kebijakan, target cakupan imunisasi nasional, serta strategi alokasi sumber daya dan logistik imunisasi jangka menengah.",
        "related_documents": [],
        "page_filter": None,
    },
    "DOC08": {
        "document_id": "DOC08",
        "file_name": "DOC08_WHO_Good_Storage_Distribution.pdf",
        "title": "Good Storage and Distribution Practices for Medical Products (WHO Technical Report Series No. 1025, Annex 7)",
        "short_title": "WHO Good Storage and Distribution Practices",
        "publisher": "World Health Organization (WHO)",
        "publication_year": 2020,
        "document_type": "Standar Pedoman Internasional",
        "category": "Storage and Distribution",
        "description": "Pedoman internasional standar penyimpanan dan distribusi produk medis, kontrol suhu, integritas kemasan, dan keamanan transportasi obat.",
        "related_documents": [],
        "page_filter": None,
    },
    "DOC09": {
        "document_id": "DOC09",
        "file_name": "DOC09_WHO_Vaccine_Management_Handbook.pdf",
        "title": "WHO Vaccine Management Handbook: How to Monitor Temperatures in the Vaccine Supply Chain (Module VMH-E3-01.1)",
        "short_title": "WHO Vaccine Management Handbook - Temperature Monitoring",
        "publisher": "World Health Organization (WHO)",
        "publication_year": 2017,
        "document_type": "Panduan Teknis Internasional",
        "category": "Vaccine Management & Cold Chain",
        "description": "Protokol monitoring suhu pada rantai pasok vaksin, penggunaan indikator VVM, data logger, alarm suhu, dan tindakan mitigasi ekskursi suhu.",
        "related_documents": [],
        "page_filter": None,
    },
    "DOC10": {
        "document_id": "DOC10",
        "file_name": "DOC10_WHO_Vaccine_Shipping_Guidelines.pdf",
        "title": "WHO Guidelines for the International Packaging and Shipping of Vaccines (WHO/IVB/20.08)",
        "short_title": "WHO Packaging and Shipping of Vaccines Guidelines",
        "publisher": "World Health Organization (WHO)",
        "publication_year": 2020,
        "document_type": "Standar Pedoman Pengiriman Internasional",
        "category": "Medical Product Distribution & Cold Chain",
        "description": "Spesifikasi isolasi termal, cold box, pengondisian ice packs/cool packs, pemantauan rute transportasi, dan jaminan keamanan pengiriman vaksin biologis.",
        "related_documents": [],
        "page_filter": None,
    },
}


def get_document_metadata(doc_id_or_filename: str) -> Optional[Dict[str, Any]]:
    """
    Mengambil metadata dokumen berdasarkan ID (DOC01) atau nama file.
    """
    if doc_id_or_filename in OFFICIAL_DOCUMENTS_REGISTRY:
        return OFFICIAL_DOCUMENTS_REGISTRY[doc_id_or_filename]
    for doc in OFFICIAL_DOCUMENTS_REGISTRY.values():
        if doc["file_name"] == doc_id_or_filename:
            return doc
    return None
