# CAAS Fees Legislation Assistant

A Retrieval-Augmented Generation (RAG) Streamlit app that helps CAAS finance
officers search and understand legislation on fees collected by CAAS.

## 📁 Project Structure

```
caas-legislation-rag/
├── app.py                      # Main entry point: disclaimer + login
├── pages/
│   ├── 1_Chat_Assistant.py     # RAG Q&A chat (Admin + User)
│   ├── 2_Admin_Upload.py       # Document upload / delete / re-index (Admin only)
│   ├── 3_About_Us.py           # Project scope, objectives, data sources
│   └── 4_Methodology.py        # Data flow + flowcharts for each use case
├── utils/
│   ├── auth.py                 # Login/role gate used by every page
│   ├── security.py             # System prompt + prompt-injection guardrails
│   ├── document_loader.py      # Upload, list, delete, chunk, embed, index
│   └── rag_engine.py           # Retrieval + grounded answer generation
├── data/
│   ├── raw_docs/                # Uploaded PDF/DOCX/TXT source files
│   └── vector_store/            # Persisted FAISS index
├── .env                         # Local secrets (NOT committed — see .gitignore)
├── .env.example                 # Template for required environment variables
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 1. Local Setup (Python virtual environment)

```bash
# 1. Clone / unzip the project, then cd into it
cd caas-legislation-rag

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env and fill in:
#   OPENAI_API_KEY=sk-...
#   ADMIN_USERNAME / ADMIN_PASSWORD
#   USER_USERNAME / USER_PASSWORD

# 5. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## 2. First-Time Use

1. Log in as **Admin** (credentials from `.env`).
2. Go to **📤 Admin Upload**, upload one or more CAAS fee legislation
   documents (PDF/DOCX/TXT), then click **🔄 Rebuild Index**.
3. Log out and log back in as **User** (or stay as Admin) and go to
   **💬 Chat Assistant** to ask questions, e.g.:
   > "What is the fee for renewing an Air Operator Certificate?"
4. Answers include the source document name so officers can verify against
   the original legislation.

## 3. Running with Docker

```bash
# Build and run with docker-compose (recommended — persists data/ automatically)
docker compose up --build

# OR build/run manually
docker build -t caas-legislation-app .
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data caas-legislation-app
```

Visit `http://localhost:8501`.

> The `-v $(pwd)/data:/app/data` volume mount is important — without it,
> uploaded documents and the FAISS index are lost when the container stops.

## 4. Password Protection

The assignment recommends password-protecting the deployed app. This is
handled two ways here:
- **App-level login** (built in): hardcoded Admin/User accounts via `.env`.
- **Optional platform-level protection**, if deploying to Streamlit
  Community Cloud: use `st.secrets` (via `.streamlit/secrets.toml`, which
  is gitignored) instead of a `.env` file, and consider restricting the app
  to invited viewers in the sharing settings.

## 5. Notes on Safety / Prompt Injection

- All user chat input is screened for common override phrases before being
  sent to the LLM (`utils/security.py`).
- Retrieved document text is wrapped in `<document_excerpt>` tags and the
  system prompt explicitly instructs the model to treat it as reference
  data only — this reduces the risk of instructions hidden inside an
  uploaded document being followed by the LLM.
- The model is instructed to answer only from retrieved context and to
  decline unrelated or advice-seeking requests (see the Methodology page
  in-app for the full data flow).

## 6. Extending the App

- Swap `OpenAIEmbeddings` / `ChatOpenAI` in `utils/document_loader.py` and
  `utils/rag_engine.py` for another provider if needed.
- Swap FAISS for Chroma by changing the vector store import if preferred.
- Add persistent (file/DB-backed) question history if history needs to
  survive across sessions, not just within one.
