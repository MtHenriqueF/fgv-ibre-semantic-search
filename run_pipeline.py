"""Entry point for the project pipeline."""

from src.chunking import run_chunking_pipeline
from src.cleaning import run_cleaning_pipeline
from src.config import CHROMA_DB_DIR, CLEAN_NEWS_PATH
from src.vector_store import index_chunks


def main() -> None:
    """Run cleaning when needed, then chunk and index the cleaned news."""
    if CLEAN_NEWS_PATH.exists():
        print(f"Reutilizando dados limpos existentes: {CLEAN_NEWS_PATH}")
    else:
        print("Dados limpos não encontrados. Executando limpeza...")
        run_cleaning_pipeline()

    chunks = run_chunking_pipeline()
    print(f"Chunks gerados: {len(chunks)}")

    collection = index_chunks(chunks)
    print(f"Indexação vetorial concluída. Coleção: {collection.name}")
    print(f"ChromaDB salvo em: {CHROMA_DB_DIR}")


if __name__ == "__main__":
    main()
