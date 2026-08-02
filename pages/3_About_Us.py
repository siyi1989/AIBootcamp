import streamlit as st

from utils.auth import require_login


st.title("ℹ️ About This Project")

st.markdown(
    """
### Project Scope
The **CAAS Fees Legislation Assistant** is a proof-of-concept Retrieval-Augmented
Generation (RAG) tool built for finance officers within the Civil Aviation
Authority of Singapore (CAAS). It helps officers quickly understand and
locate information on the various fees CAAS collects (e.g. licensing fees,
certification fees, airport charges) as set out in relevant legislation and
official notices.

### Objectives
- Give finance officers a fast, conversational way to search fee-related
  legislation instead of manually reading long PDF documents.
- Reduce the time other officers spend looking up which legislation governs
  a specific fee.
- Provide a controlled way (Admin-only) to keep the underlying document set
  current as legislation is updated.

### Data Sources
- Legislation, regulations, and official notices relating to fees collected
  by CAAS, uploaded by an Admin as PDF, DOCX, or TXT files.
- All documents are stored locally in the app's `data/raw_docs` folder and
  indexed into a FAISS vector store for retrieval.

### Key Features
- 🔐 Role-based login (Admin)
- 📤 Admin-only document upload, deletion, and re-indexing
- 💬 Natural-language Q&A over indexed legislation with cited sources
- 🕘 In-session question history
- 🛡️ Guardrails against prompt injection and off-topic requests

### Intended Users
- **Admin:** manages the document library (upload / delete / rebuild index).
- **User:** searches and asks questions about fee legislation.
"""
)
