import os
import shutil
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from langchain_qdrant import QdrantVectorStore
except ImportError:  # pragma: no cover - optional dependency
    QdrantClient = None
    models = None
    QdrantVectorStore = None

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data/raw_docs"
INDEX_DIR = BASE_DIR / "data/vector_store"

LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
}

# Free-tier limit is 100 embedding requests/minute — stay comfortably under it
BATCH_SIZE = 50
SECONDS_BETWEEN_BATCHES = 0


class QdrantStoreAdapter:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def similarity_search_with_relevance_scores(self, query, k=12):
        results = self.vector_store.similarity_search_with_score(query, k=k)
        adapted = []
        for doc, score in results:
            similarity = max(0.0, min(1.0, 1.0 - score))
            adapted.append((doc, similarity))
        return adapted


def ensure_data_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def list_documents():
    ensure_data_dirs()
    return sorted(p.name for p in DATA_DIR.glob("*") if p.suffix.lower() in LOADERS)


def has_documents():
    ensure_data_dirs()
    return any(p.suffix.lower() in LOADERS for p in DATA_DIR.glob("*"))


def has_vector_store():
    ensure_data_dirs()
    return any((INDEX_DIR / name).exists() for name in ["index.faiss", "index.pkl"])


def clear_vector_store():
    ensure_data_dirs()
    if not INDEX_DIR.exists():
        return False

    for child in INDEX_DIR.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)
    return True


def get_persistence_status():
    ensure_data_dirs()
    return {
        "documents": list_documents(),
        "has_index": has_vector_store(),
    }


def save_uploaded_file(uploaded_file):
    ensure_data_dirs()
    dest = DATA_DIR / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest


def delete_document(filename):
    path = DATA_DIR / filename
    if path.exists():
        path.unlink()
    clear_vector_store()
    return not path.exists()


def load_all_documents():
    docs = []
    for path in DATA_DIR.glob("*"):
        loader_cls = LOADERS.get(path.suffix.lower())
        if not loader_cls:
            continue
        loader = loader_cls(str(path))
        loaded = loader.load()
        for d in loaded:
            d.metadata["source"] = path.name
        docs.extend(loaded)
    return docs


def get_embeddings():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Configure it before building or loading the vector store.")

    return OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)


def _get_streamlit_secret(name):
    try:
        import streamlit as st
    except Exception:
        return None

    if st is None:
        return None

    secrets = getattr(st, "secrets", None)
    if secrets is None:
        return None

    if hasattr(secrets, "get"):
        return secrets.get(name)
    return getattr(secrets, name, None)


def get_qdrant_config():
    return {
        "url": os.getenv("QDRANT_URL") or _get_streamlit_secret("QDRANT_URL") or "",
        "api_key": os.getenv("QDRANT_API_KEY") or _get_streamlit_secret("QDRANT_API_KEY") or "",
        "collection_name": os.getenv("QDRANT_COLLECTION_NAME") or _get_streamlit_secret("QDRANT_COLLECTION_NAME") or "caas-documents",
    }


def use_qdrant():
    cfg = get_qdrant_config()
    return bool(cfg["url"]) and QdrantClient is not None and QdrantVectorStore is not None and models is not None


@lru_cache(maxsize=1)
def get_qdrant_client():
    if not use_qdrant():
        return None

    cfg = get_qdrant_config()
    return QdrantClient(url=cfg["url"], api_key=cfg["api_key"] or None)


def ensure_qdrant_collection(client, collection_name):
    if client is None:
        return False

    collections = client.get_collections().collections
    if any(collection.name == collection_name for collection in collections):
        return True

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
    )
    return True


def build_vector_store(progress_callback=None):
    """Build the vector index from every supported file in data/raw_docs.
    Uses Qdrant Cloud when configured, otherwise falls back to a local FAISS index."""
    ensure_data_dirs()
    docs = load_all_documents()
    if not docs:
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    chunks = splitter.split_documents(docs)

    if use_qdrant():
        embeddings = get_embeddings()
        client = get_qdrant_client()
        cfg = get_qdrant_config()
        ensure_qdrant_collection(client, cfg["collection_name"])

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=cfg["collection_name"],
            embedding=embeddings,
        )
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            if progress_callback:
                progress_callback(batch_num, total_batches)
            batch_texts = [chunk.page_content for chunk in batch]
            batch_metadatas = [dict(chunk.metadata) for chunk in batch]
            vector_store.add_texts(batch_texts, metadatas=batch_metadatas)
            if i + BATCH_SIZE < len(chunks):
                time.sleep(SECONDS_BETWEEN_BATCHES)

        return QdrantStoreAdapter(vector_store)

    embeddings = get_embeddings()
    vector_store = None
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        if progress_callback:
            progress_callback(batch_num, total_batches)

        if vector_store is None:
            vector_store = FAISS.from_documents(batch, embeddings)
        else:
            vector_store.add_documents(batch)

        if i + BATCH_SIZE < len(chunks):
            time.sleep(SECONDS_BETWEEN_BATCHES)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(INDEX_DIR))
    return vector_store


def load_vector_store():
    ensure_data_dirs()

    if use_qdrant():
        try:
            client = get_qdrant_client()
            cfg = get_qdrant_config()
            if client is None:
                return None
            collections = client.get_collections().collections
            if not any(collection.name == cfg["collection_name"] for collection in collections):
                if has_documents():
                    return build_vector_store()
                return None

            embeddings = get_embeddings()
            vector_store = QdrantVectorStore(
                client=client,
                collection_name=cfg["collection_name"],
                embeddings=embeddings,
            )
            return QdrantStoreAdapter(vector_store)
        except Exception:
            return None

    if not has_vector_store():
        if has_documents():
            try:
                return build_vector_store()
            except Exception:
                return None
        return None

    try:
        embeddings = get_embeddings()
    except Exception:
        return None

    try:
        return FAISS.load_local(
            str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
        )
    except Exception:
        return None