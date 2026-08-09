# Client Deployment Guide

This project now ships with a single-command Docker deployment suitable for another laptop or server.

## Prerequisites on the client machine

- Docker Desktop or Docker Engine + Docker Compose
- Internet access for first-time model downloads
- NVIDIA GPU with NVIDIA Container Toolkit is optional for faster Ollama inference

## First-Time Setup

1. Copy the entire project folder to the client machine.
2. In the project root, create `backend/.env`:

```text
SECRET_KEY=replace-with-a-random-48-byte-secret
```

3. Start everything:

```bash
docker compose up --build
```

On first run, Compose downloads Ollama and pulls the configured models. This can take several minutes depending on internet speed.

## Models

Default Ollama models:

- Chat: `qwen3:8b`
- Embeddings: `nomic-embed-text:latest`

Change models with environment variables in `backend/.env`:

```text
OLLAMA_CHAT_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
```

## Access

- App: `http://localhost`
- API: `http://localhost/api`

## Optional: GPU acceleration

If the client machine has an NVIDIA GPU and NVIDIA Container Toolkit is installed, uncomment the `deploy.resources` block under `ollama` in `docker-compose.yml`.

## Data

Persistent volumes are used for:

- Ollama models
- Chroma vector storage
- Uploaded images
- SQLite database
