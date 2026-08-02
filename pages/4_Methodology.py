import streamlit as st
import graphviz

from utils.auth import require_login


st.title("🔍 Methodology")

st.markdown(
    """
This app has two main use cases, each with its own data flow:

1. **Document Ingestion & Indexing** (Admin)
2. **Chat / Intelligent Search** (Admin & User)
"""
)

st.subheader("1️⃣ Document Ingestion & Indexing Flow")
g1 = graphviz.Digraph()
g1.attr(rankdir="LR")
g1.node("A", "Admin uploads\nPDF / DOCX / TXT")
g1.node("B", "File saved to\ndata/raw_docs/")
g1.node("C", "Admin clicks\n'Rebuild Index'")
g1.node("D", "Documents parsed\n(PyPDFLoader / Docx2txtLoader / TextLoader)")
g1.node("E", "Text split into\nchunks (1000 chars, 150 overlap)")
g1.node("F", "Chunks embedded\n(OpenAI Embeddings)")
g1.node("G", "FAISS index built &\nsaved to data/vector_store/")
g1.edges(["AB", "BC", "CD", "DE", "EF", "FG"])
st.graphviz_chart(g1)

st.markdown(
    """
- **Upload:** Admin selects one or more documents via the file uploader.
- **Storage:** Raw files are kept in `data/raw_docs/` so they can be
  re-indexed or removed later.
- **Chunking:** Long documents are split into overlapping chunks so relevant
  sections can be retrieved precisely, even from long legislation.
- **Embedding & Indexing:** Each chunk is converted to a vector embedding
  and stored in a local FAISS index for fast similarity search.
"""
)

st.subheader("2️⃣ Chat / Intelligent Search Flow")
g2 = graphviz.Digraph()
g2.attr(rankdir="LR")
g2.node("H", "User types\na question")
g2.node("I", "Input screened\n(prompt-injection check)")
g2.node("J", "FAISS similarity\nsearch (top-k chunks)")
g2.node("K", "Chunks wrapped as\n'context', not instructions")
g2.node("L", "LLM answers using\nsystem prompt + context")
g2.node("M", "Answer + cited\nsources shown to user")
g2.node("N", "Saved to session\nquestion history")
g2.edges(["HI", "IJ", "JK", "KL", "LM", "MN"])
st.graphviz_chart(g2)

st.markdown(
    """
- **Screening:** User input is checked against known prompt-injection
  phrases before being sent to the retriever/LLM.
- **Retrieval:** The question is embedded and compared against the FAISS
  index to fetch the most relevant document chunks.
- **Safe context wrapping:** Retrieved text is wrapped in explicit
  `<document_excerpt>` tags, and the system prompt instructs the LLM to
  treat it as reference data only — never as commands. This mitigates
  indirect prompt injection hidden inside uploaded documents.
- **Grounded answer:** The LLM is instructed to answer only from the
  provided context and to cite the source document for every fact.
- **History:** Each question/answer pair is stored in `st.session_state`
  for the duration of the session and shown in the sidebar.

### Tech Stack
| Layer | Technology |
|---|---|
| UI | Streamlit (multi-page) |
| Orchestration | LangChain |
| Vector Store | FAISS |
| Embeddings & LLM | OpenAI (`text-embedding-ada-002`, `gpt-4o-mini`) |
| Document Parsing | PyPDF, docx2txt |
| Deployment | Docker |
"""
)
