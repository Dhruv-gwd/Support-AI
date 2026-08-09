# SupportAI — AI Customer Support Platform

A self-hosted AI customer support platform with RAG (Retrieval-Augmented Generation), multi-format document processing, and multi-tenant support. Runs entirely on local infrastructure via Ollama — no data leaves the deployment machine.

## Features

- **AI Chat** — real-time customer support with conversation history
- **Document Processing** — upload PDF, DOCX, TXT, CSV, Excel, Markdown, HTML files
- **RAG Pipeline** — semantic search with ChromaDB + local Ollama embeddings
- **Multi-Tenancy** — each signup gets an isolated tenant; documents and chat retrieval are scoped per tenant
- **User Authentication** — JWT-based login/register, with the first user of a tenant automatically becoming that tenant's admin
- **Conversation Persistence** — SQLite database for chat history
- **Admin Dashboard** — upload, list, and delete documents
- **Rate Limiting** — per-route request throttling on login, register, chat, and document endpoints
- **Docker Ready** — one-command deployment with Docker Compose

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy + SQLite
- **Ollama** (local LLM) — chat generation and embeddings, both fully local
- ChromaDB (vector store)
- JWT authentication
- SlowAPI (rate limiting)

### Frontend
- React + Vite
- Tailwind CSS
- React Router
- Axios

> **Note:** Some service filenames (`gemini_service.py`) are leftover from an earlier Gemini-API-based version of this project. The code inside those files now calls Ollama exclusively — there is no Gemini API dependency and no `GEMINI_API_KEY` anywhere in this codebase. Renaming the files is a pending cleanup item.

## Quick Start (Docker — recommended)

```bash
# from the project root
docker compose up --build
```

On first run, Compose pulls the Ollama chat and embedding models — this can take several minutes.

Access the app at `http://localhost`.

### Verify the stack came up correctly

```bash
docker compose ps
```
Expect `backend`, `frontend`, `ollama` all `Up`/healthy, and `init-models` as `Exited (0)`.

## Manual Setup (without Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create `backend/.env`:
```
SECRET_KEY=replace-with-a-random-48-byte-secret
```

Run:
```bash
uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000`.

You'll also need Ollama running locally with the configured models pulled:
```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

### 3. Use the app

1. Go to `/register` and create an account — you'll be made admin of your own tenant automatically.
2. Go to **Admin** to upload documents.
3. Go to **Chat** to ask questions about your documents.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | JWT signing secret | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time (minutes) | 60 |
| `MAX_FILE_SIZE_MB` | Max upload size | 10 |
| `RATE_LIMIT_PER_MINUTE` | Requests/minute on login, register, chat, upload, list, delete | 30 |
| `OLLAMA_BASE_URL` | Ollama API base URL | `http://ollama:11434` |
| `OLLAMA_CHAT_MODEL` | Chat/generation model | `qwen3:8b` (`qwen2.5:3b` in Docker Compose) |
| `OLLAMA_EMBEDDING_MODEL` | Embedding model | `nomic-embed-text:latest` |

## API Endpoints

### Authentication
- `POST /api/auth/register` — register new user (first user of a tenant becomes admin) — rate limited
- `POST /api/auth/login` — login (returns JWT) — rate limited
- `GET /api/auth/me` — current user info
- `GET /api/auth/conversations` / `POST /api/auth/conversations` — list/create conversations
- `GET /api/auth/conversations/{id}/messages` — get conversation messages
- `DELETE /api/auth/conversations/{id}` — delete conversation

### Chat
- `POST /api/chat` — send message (requires auth, rate limited)
  - Body: `{ "message": "string", "conversation_id": "optional int" }`

### Documents (admin only)
- `POST /api/documents/upload` — upload document; re-uploading an existing filename replaces it rather than duplicating chunks — rate limited
- `GET /api/documents` — list documents for the current tenant — rate limited
- `DELETE /api/documents/{filename}` — delete a document — rate limited

### Images
- `GET /api/images/{image_name}` — serve an image extracted from a document (tenant-scoped)

## Project Structure

```
SupportAI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # Auth endpoints, admin bootstrap logic
│   │   │   ├── chat.py          # Chat endpoint
│   │   │   └── documents.py     # Document upload/list/delete
│   │   ├── models/
│   │   │   ├── database.py      # SQLAlchemy models
│   │   │   └── schemas.py       # Pydantic schemas
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── chunking_service.py
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py   # Ollama embeddings
│   │   │   ├── gemini_service.py      # Ollama chat generation (legacy filename)
│   │   │   ├── image_store.py
│   │   │   ├── rag_service.py
│   │   │   └── vector_store_service.py
│   │   ├── config.py
│   │   ├── limiter.py            # Shared rate limiter instance
│   │   └── main.py
│   ├── make_admin.py             # Manual admin-promotion script (legacy; no longer required for new signups)
│   ├── migrate_tenants.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/ ...
├── docker-compose.yml
├── CLIENT_SETUP.md
└── README.md
```

## Known Limitations

- **Image-only uploads** (`.png`/`.jpg`/etc.) are stored but not OCR'd or embedded — chat cannot currently answer questions about their content.
- **Chat latency** is CPU-bound and dependent on the configured Ollama model; for live-chat use cases, consider GPU passthrough or a smaller model.
- **Admin/Users/Settings tabs** beyond document management are placeholders.

## License

MIT