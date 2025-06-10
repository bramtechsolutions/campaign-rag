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
    data = json.loads(await file.read())
    messages = data.get('messages', [])

    for m in messages:
        if m.get('type') == 'character_definition':
            name = m['author']['name'].replace(' ', '_')
            with open(os.path.join(CHAR_DIR, f"{name}.json"), 'w') as f:
                json.dump({'id': m['id'], 'name': m['author']['name'], 'sheet': m.get('content'), 'timestamp': m['timestamp']}, f, indent=2)

    sessions = {}
    for m in messages:
        date = m['timestamp'][:10]
        sessions.setdefault(date, []).append({'id': m['id'], 'author': m['author']['name'], 'text': m.get('content',''), 'timestamp': m['timestamp']})
    for date, entries in sessions.items():
        with open(os.path.join(SESSION_DIR, f"session_{date}.json"), 'w') as f:
            json.dump({'session_date': date, 'entries': entries}, f, indent=2)

    for m in messages:
        if m.get('channel_type') == 'lore':
            title = m['content'].split('\n',1)[0]
            with open(os.path.join(WORLD_DIR, f"{title}.json"), 'w') as f:
                json.dump({'id': m['id'], 'title': title, 'content': m.get('content'), 'timestamp': m['timestamp']}, f, indent=2)

    return {"status":"success","characters":len(os.listdir(CHAR_DIR)),"sessions":len(os.listdir(SESSION_DIR)),"world_entries":len(os.listdir(WORLD_DIR))}

@app.get("/ask")
async def ask(q: str):
    results = []
    for fname in os.listdir(CHAR_DIR):
        text = open(os.path.join(CHAR_DIR, fname)).read()
        if q.lower() in text.lower():
            results.append({'type':'character','file':fname})
    for fname in os.listdir(SESSION_DIR):
        text = open(os.path.join(SESSION_DIR, fname)).read()
        if q.lower() in text.lower():
            results.append({'type':'session','file':fname})
    for fname in os.listdir(WORLD_DIR):
        text = open(os.path.join(WORLD_DIR, fname)).read()
        if q.lower() in text.lower():
            results.append({'type':'world','file':fname})
    return {'query':q,'results':results}
