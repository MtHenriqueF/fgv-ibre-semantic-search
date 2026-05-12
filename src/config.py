"""Project configuration constants and paths."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"

RAW_NEWS_PATH = RAW_DATA_DIR / "noticias_brutas.json"
CLEAN_NEWS_PATH = PROCESSED_DATA_DIR / "noticias_limpas.json"
CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks.jsonl"
CLEANING_REPORT_PATH = OUTPUTS_DIR / "cleaning_report.csv"
EVALUATION_RESULTS_PATH = OUTPUTS_DIR / "evaluation_results.csv"

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_TOP_K = 5
CHROMA_COLLECTION_NAME = "fgv_ibre_news_chunks"
