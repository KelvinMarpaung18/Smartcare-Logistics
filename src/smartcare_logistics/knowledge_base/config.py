"""
Modul Konfigurasi Knowledge Base & Search SmartCare Logistics.
Mengatur parameter korpus, chunking, embedding, ChromaDB, dan retrieval.
"""

from pathlib import Path

# Path direktori utama proyek
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Path direktori korpus dan penyimpanan pengetahuan
KB_DIR = BASE_DIR / "knowledge_base"
DOCUMENTS_DIR = KB_DIR / "documents"
PROCESSED_DIR = KB_DIR / "processed"
CHUNKS_DIR = KB_DIR / "chunks"
CHROMA_DB_DIR = KB_DIR / "chroma_db"
LEXICAL_INDEX_DIR = KB_DIR / "lexical_index"
BENCHMARK_DIR = KB_DIR / "benchmark"
REPORTS_DIR = KB_DIR / "reports"

# Nama model embedding Sentence-Transformers
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
EMBEDDING_DIMENSION = 768
MAX_TOKEN_LENGTH = 512

# Prefix wajib untuk model E5
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "

# Nama koleksi ChromaDB
CHROMA_COLLECTION_NAME = "smartcare_knowledge_base"

# Konfigurasi default chunking (hasil eksperimen)
DEFAULT_CHUNK_SIZE = 300  # kata
DEFAULT_CHUNK_OVERLAP = 50  # kata

# Eksperimen variasi chunking untuk perbandingan
CHUNKING_EXPERIMENTS = [
    {"name": "Config_A_200_30", "chunk_size": 200, "overlap": 30},
    {"name": "Config_B_300_50", "chunk_size": 300, "overlap": 50},
    {"name": "Config_C_400_75", "chunk_size": 400, "overlap": 75},
]

# Parameter Hybrid Search (Reciprocal Rank Fusion)
RRF_K = 60
WEIGHT_DENSE = 0.6
WEIGHT_BM25 = 0.4

# Threshold Cosine Distance untuk deteksi Out-of-Domain (OOD)
# Berdasarkan kalibrasi empiris embedding E5: query in-domain > 0.81, query OOD <= 0.795
OOD_DISTANCE_THRESHOLD = 0.20
OOD_SIMILARITY_THRESHOLD = 0.80

# Default retrieval limit
DEFAULT_TOP_K = 5
