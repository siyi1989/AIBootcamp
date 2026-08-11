import streamlit as st

from utils.auth import require_login
from utils.document_loader import (
    list_documents,
    save_uploaded_file,
    delete_document,
    build_vector_store,
    get_persistence_status,
)


require_login(allowed_roles=["Admin"])

st.title("📤 Admin — Manage Legislation Documents")
st.caption(
    "Upload PDF, DOCX, or TXT files containing CAAS fee legislation. "
    "Only Admins can access this page."
)

st.info(
    "If Qdrant Cloud is configured, uploaded chunks will be stored there for persistence. "
    "Otherwise the app will keep using the local FAISS index."
)

status = get_persistence_status()
if status["documents"]:
    if status["has_index"]:
        st.success(
            "Saved documents and a persisted vector index were found. New sessions will reuse them until you choose to rebuild."
        )
    else:
        st.warning(
            "Documents are saved locally, but the vector index is not available yet. The app will build it automatically when needed, or you can rebuild it now."
        )
else:
    st.info("No documents have been uploaded yet. Upload files to keep them for future sessions.")

uploaded_files = st.file_uploader(
    "Upload documents",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if uploaded_files:
    for f in uploaded_files:
        save_uploaded_file(f)
    st.success(
        f"Saved {len(uploaded_files)} file(s). They will remain on disk for future sessions. "
        "Existing vectors stay in place until you click 'Rebuild Index' to refresh them."
    )

st.divider()
st.subheader("📚 Current Documents")
docs = list_documents()
if docs:
    for d in docs:
        col1, col2 = st.columns([4, 1])
        col1.write(d)
        if col2.button("🗑️ Delete", key=f"del_{d}"):
            delete_document(d)
            st.rerun()
else:
    st.info("No documents uploaded yet.")

st.divider()
if st.button("🔄 Rebuild Index", type="primary"):
    progress_bar = st.progress(0, text="Starting...")

    def update_progress(batch_num, total_batches):
        progress_bar.progress(
            batch_num / total_batches,
            text=f"Embedding batch {batch_num} of {total_batches}...",
        )

    vs = build_vector_store(progress_callback=update_progress)
    progress_bar.empty()

    if vs is None:
        st.warning("No documents to index yet.")
    else:
        st.success(
            "Index rebuilt successfully. Users can now query the updated documents."
        )