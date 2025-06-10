from fastapi import FastAPI, UploadFile, File, HTTPException
import json
import os
import string
from typing import List, Dict

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "RAG Ingestion Service: POST to /ingest with your JSON export file."}

BASE_DIR = os.path.dirname(__file__)
CHAR_DIR = os.path.join(BASE_DIR, 'characters')
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
WORLD_DIR = os.path.join(BASE_DIR, 'world_data')

for d in (CHAR_DIR, SESSION_DIR, WORLD_DIR):
    os.makedirs(d, exist_ok=True)

@app.post("/ingest")
async def ingest_export(file: UploadFile = File(...)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files allowed.")
    content = await file.read()
    export = json.loads(content)
    messages = export.get('messages', [])

    # Extract characters based on message type or content marker
    for m in messages:
        if m.get('type') == 'character_definition' or 'sheet' in m:
            name = m['author']['name'].replace(' ', '_')
            path = os.path.join(CHAR_DIR, f"{name}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'id': m.get('id'),
                    'name': m['author']['name'],
                    'sheet': m.get('content', ''),
                    'timestamp': m.get('timestamp')
                }, f, ensure_ascii=False, indent=2)

    # Extract sessions by date
    sessions: Dict[str, List[Dict]] = {}
    for m in messages:
        ts = m.get('timestamp', '')
        date = ts[:10] if len(ts) >= 10 else 'unknown'
        sessions.setdefault(date, []).append({
            'id': m.get('id'),
            'author': m.get('author', {}).get('name', ''),
            'text': m.get('content', ''),
            'timestamp': ts
        })
    for date, entries in sessions.items():
        path = os.path.join(SESSION_DIR, f"session_{date}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'session_date': date, 'entries': entries}, f, ensure_ascii=False, indent=2)

    # Extract world data by channel name 'lore'
    for m in messages:
        channel = m.get('channel', {}).get('name', '').lower()
        if channel == 'lore':
            title = m.get('content', '').split('\n', 1)[0][:50].replace(' ', '_')
            path = os.path.join(WORLD_DIR, f"{title}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'id': m.get('id'),
                    'title': title,
                    'content': m.get('content', ''),
                    'timestamp': m.get('timestamp')
                }, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "characters": len(os.listdir(CHAR_DIR)),
        "sessions": len(os.listdir(SESSION_DIR)),
        "world_entries": len(os.listdir(WORLD_DIR))
    }

@app.get("/ask")
async def ask(q: str):
    # Normalize and strip punctuation
    clean_q = q.lower().strip()
    clean_q = clean_q.translate(str.maketrans('', '', string.punctuation))

    results = []

    # Search characters
    for fname in os.listdir(CHAR_DIR):
        if not fname.endswith('.json'):
            continue
        data = json.load(open(os.path.join(CHAR_DIR, fname), 'r', encoding='utf-8'))
        text = data.get('sheet', '').lower()
        if clean_q in text.translate(str.maketrans('', '', string.punctuation)):
            results.append({'type': 'character', 'file': fname})

    # Search sessions
    for fname in os.listdir(SESSION_DIR):
        if not fname.endswith('.json'):
            continue
        entries = json.load(open(os.path.join(SESSION_DIR, fname), 'r', encoding='utf-8')).get('entries', [])
        combined = ' '.join(e.get('text', '') for e in entries).lower()
        if clean_q in combined.translate(str.maketrans('', '', string.punctuation)):
            results.append({'type': 'session', 'file': fname})

    # Search world data
    for fname in os.listdir(WORLD_DIR):
        if not fname.endswith('.json'):
            continue
        data = json.load(open(os.path.join(WORLD_DIR, fname), 'r', encoding='utf-8'))
        content = data.get('content', '').lower()
        if clean_q in content.translate(str.maketrans('', '', string.punctuation)):
            results.append({'type': 'world', 'file': fname})

    return {'query': q, 'results': results}
