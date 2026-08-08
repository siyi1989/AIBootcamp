import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def list_documents():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in DATA_DIR.glob("*") if p.suffix.lower() in LOADERS)


def save_uploaded_file(uploaded_file):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_DIR / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest


def delete_document(filename):
    path = DATA_DIR / filename
    if path.exists():
        path.unlink()


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

def build_vector_store(progress_callback=None):
    """(Re)build the FAISS index from every supported file in data/raw_docs.
    Embeds in small batches with pauses to stay under free-tier rate limits."""
    docs = load_all_documents()
    if not docs:
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    chunks = splitter.split_documents(docs)

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

        # Pause between batches (skip the pause after the very last batch)
        if i + BATCH_SIZE < len(chunks):
            time.sleep(SECONDS_BETWEEN_BATCHES)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(INDEX_DIR))
    return vector_store


def load_vector_store():
    if not (INDEX_DIR / "index.faiss").exists():
        return None
    embeddings = get_embeddings()
    return FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )