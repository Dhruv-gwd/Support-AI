# SupportAI - AI Customer Support Platform

A production-ready AI customer support platform with RAG (Retrieval-Augmented Generation), document processing, and multi-user support.

## Features

- **AI Chat**: Real-time customer support with conversation history
- **Document Processing**: Upload PDF, DOCX, TXT, CSV, Excel, Markdown, HTML files
- **RAG Pipeline**: Semantic search with ChromaDB + Google Gemini embeddings
- **Image Extraction**: Automatically extract and display images from documents
- **User Authentication**: JWT-based login/register with protected routes
- **Conversation Persistence**: SQLite database for chat history
- **Admin Dashboard**: Upload, manage, and delete documents
- **Rate Limiting**: Built-in request rate limiting
- **Docker Ready**: One-command deployment with Docker Compose

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy + SQLite
- Google Gemini API (embeddings + generation)
- ChromaDB (vector store)
- JWT authentication
- SlowAPI (rate limiting)

### Frontend
- React + Vite
- Tailwind CSS
- React Router
- Axios

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### 1. Clone and Setup Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
GEMINI_API_KEY=your-actual-gemini-api-key
SECRET_KEY=change-this-to-a-random-string-in-production
```

### 3. Run Backend

```bash
uvicorn app.main:app --reload
```

Backend will run at `http://localhost:8000`

### 4. Setup Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at `http://localhost:5173`

### 5. Use the App

1. Go to `http://localhost:5173/register` to create an account
2. Login with your credentials
3. Go to **Admin** to upload documents
4. Go to **Chat** to ask questions about your documents

## Docker Deployment

```bash
# Set your Gemini API key
export GEMINI_API_KEY=your-key-here

# Start all services
docker compose up --build
```

Access at `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT)
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/conversations` - List user conversations
- `POST /api/auth/conversations` - Create new conversation
- `GET /api/auth/conversations/{id}/messages` - Get conversation messages
- `DELETE /api/auth/conversations/{id}` - Delete conversation

### Chat
- `POST /api/chat` - Send message (requires auth)
- Request body: `{ "message": "string", "conversation_id": "optional int" }`

### Documents
- `POST /api/documents/upload` - Upload document (requires auth)
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{filename}` - Delete document

### Images
- `GET /api/images/{image_name}` - Serve extracted document image

## Project Structure

```
SupportAI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── chat.py          # Chat endpoint
│   │   │   └── documents.py     # Document management
│   │   ├── models/
│   │   │   ├── database.py      # SQLAlchemy models
│   │   │   └── schemas.py       # Pydantic schemas
│   │   ├── services/
│   │   │   ├── auth_service.py  # JWT utilities
│   │   │   ├── chunking_service.py
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── gemini_service.py
│   │   │   ├── image_store.py
│   │   │   ├── rag_service.py
│   │   │   └── vector_store_service.py
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/Navbar.jsx
│   │   ├── context/
│   │   │   ├── AuthContext.jsx
│   │   │   ├── ChatContext.jsx
│   │   │   └── DocsContext.jsx
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx
│   │   │   ├── AdminPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   └── RegisterPage.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `SECRET_KEY` | JWT signing secret | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | 60 |
| `MAX_FILE_SIZE_MB` | Max upload size | 10 |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | 30 |

## License

MIT
