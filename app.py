from fastapi import FastAPI, UploadFile, File, HTTPException
import json
import os
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

    # Extract characters
    for m in messages:
        if m.get('type') == 'character_definition':
            name = m['author']['name'].replace(' ', '_')
            path = os.path.join(CHAR_DIR, f"{name}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'id': m['id'],
                    'name': m['author']['name'],
                    'sheet': m.get('content'),
                    'timestamp': m['timestamp']
                }, f, ensure_ascii=False, indent=2)

    # Extract sessions
    sessions: Dict[str, List[Dict]] = {}
    for m in messages:
        date = m['timestamp'][:10]
        sessions.setdefault(date, []).append({
            'id': m['id'],
            'author': m['author']['name'],
            'text': m.get('content', ''),
            'timestamp': m['timestamp']
        })
    for date, entries in sessions.items():
        path = os.path.join(SESSION_DIR, f"session_{date}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'session_date': date, 'entries': entries}, f, ensure_ascii=False, indent=2)

    # Extract world data
    for m in messages:
        if m.get('channel_type') == 'lore':
            title = m.get('content', '').split('\n', 1)[0][:50].replace(' ', '_')
            path = os.path.join(WORLD_DIR, f"{title}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'id': m['id'],
                    'title': title,
                    'content': m.get('content'),
                    'timestamp': m['timestamp']
                }, f, ensure_ascii=False, indent=2)

    return {"status": "success", 
            "characters": len(os.listdir(CHAR_DIR)), 
            "sessions": len(os.listdir(SESSION_DIR)), 
            "world_entries": len(os.listdir(WORLD_DIR))}

@app.get("/ask")
async def ask(q: str):
    results = []
    # Search characters
    for fname in os.listdir(CHAR_DIR):
        if fname.endswith('.json'):
            data = json.load(open(os.path.join(CHAR_DIR, fname), 'r', encoding='utf-8'))
            if q.lower() in data.get('sheet', '').lower():
                results.append({'type': 'character', 'file': fname})
    # Search sessions
    for fname in os.listdir(SESSION_DIR):
        if fname.endswith('.json'):
            data = json.load(open(os.path.join(SESSION_DIR, fname), 'r', encoding='utf-8'))
            text = ' '.join(e.get('text', '') for e in data.get('entries', []))
            if q.lower() in text.lower():
                results.append({'type': 'session', 'file': fname})
    # Search world data
    for fname in os.listdir(WORLD_DIR):
        if fname.endswith('.json'):
            data = json.load(open(os.path.join(WORLD_DIR, fname), 'r', encoding='utf-8'))
            if q.lower() in data.get('content', '').lower():
                results.append({'type': 'world', 'file': fname})
    return {'query': q, 'results': results}
