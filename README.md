# README

This repository contains a FastAPI web service for ingestion of Discord chat exports into RAG-friendly JSON files.

## Local Development

Install dependencies and run the app:

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Render.com Deployment

Render.com will run the web service via `render.yaml` and the `Procfile`.

---
# Repository Structure for RAG Ingestion Pipeline

**Root files (commit these):**
```
├── app.py               # FastAPI service
├── requirements.txt     # Python dependencies
├── Procfile             # Render.com process definition
├── render.yaml          # Render.com service config
├── in-game_export.json  # Your Discord export (rename as needed)
```

**Empty folders (keep with .gitkeep):**
```
├── characters/          # Generated character JSON files
│     └── .gitkeep
├── sessions/            # Generated session_<YYYY-MM-DD>.json files
│     └── .gitkeep
└── world_data/          # Generated lore JSON files
      └── .gitkeep
```
