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
if status.get("using_qdrant"):
    st.success(
        "Qdrant Cloud is configured, and the remote collection is available for retrieval. "
        "This works even if local files are not currently present in Streamlit Cloud."
    )
    st.markdown(
        f"**Debug:** collection_exists={status.get('qdrant_collection_exists')} "
        f"| store_usable={status.get('qdrant_store_usable')}"
    )
    if status.get("qdrant_collection_exists"):
        st.caption("Qdrant collection found: 'caas-documents'.")
    else:
        st.warning(
            "Qdrant is configured but the collection has not been created yet. "
            "Click Rebuild Index to create it from the uploaded documents."
        )
elif status.get("qdrant_configured"):
    st.warning(
        "Qdrant is configured, but the app cannot connect successfully. "
        "Check your Qdrant credentials and network access."
    )
    if status.get("qdrant_error"):
        st.error(f"Qdrant error: {status['qdrant_error']}")

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
    for idx, d in enumerate(docs):
        col1, col2 = st.columns([4, 1])
        col1.write(d)
        if col2.button("🗑️ Delete", key=f"del_{idx}_{d}"):
            delete_document(d)
            st.rerun()
else:
    if status.get("using_qdrant"):
        st.warning(
            "No local documents have been uploaded in this Streamlit Cloud session. "
            "Streamlit Cloud does not persist file uploads across app restarts, so uploaded files must be re-uploaded here "
            "or the app must use your remote Qdrant collection instead."
        )
        if status.get("qdrant_collection_exists"):
            st.success(
                "Qdrant collection exists remotely, so the Chat Assistant may still answer questions from persisted vector data. "
                "Try asking a question on the Chat Assistant page."
            )
    else:
        st.info("No documents uploaded yet. Upload files to keep them for future sessions.")

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