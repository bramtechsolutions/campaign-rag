from fastapi import FastAPI, UploadFile, File, HTTPException
import json
import os
import string
from typing import List, Dict

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)
EXPORT_FILE = os.path.join(BASE_DIR, 'in-game_export.json')
CHAR_DIR = os.path.join(BASE_DIR, 'characters')
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
WORLD_DIR = os.path.join(BASE_DIR, 'world_data')

for d in (CHAR_DIR, SESSION_DIR, WORLD_DIR):
    os.makedirs(d, exist_ok=True)

def run_ingest(data: Dict):
    messages = data.get('messages', [])

    # Clear directories
    for d in (CHAR_DIR, SESSION_DIR, WORLD_DIR):
        for fname in os.listdir(d):
            if fname.endswith('.json'):
                os.remove(os.path.join(d, fname))

    # Characters
    for m in messages:
        if m.get('type') == 'character_definition' or 'sheet' in m:
            name = m['author']['name'].replace(' ', '_')
            with open(os.path.join(CHAR_DIR, f"{name}.json"), 'w', encoding='utf-8') as f:
                json.dump({'id': m.get('id'),
                           'name': m['author']['name'],
                           'sheet': m.get('content',''),
                           'timestamp': m.get('timestamp')}, f, indent=2)

    # Sessions
    sessions: Dict[str, List[Dict]] = {}
    for m in messages:
        ts = m.get('timestamp','')
        date = ts[:10] if len(ts)>=10 else 'unknown'
        sessions.setdefault(date, []).append({
            'id': m.get('id'),
            'author': m.get('author',{}).get('name',''),
            'text': m.get('content',''),
            'timestamp': ts})
    for date, entries in sessions.items():
        with open(os.path.join(SESSION_DIR, f"session_{date}.json"), 'w', encoding='utf-8') as f:
            json.dump({'session_date': date, 'entries': entries}, f, indent=2)

    # World data
    for m in messages:
        channel = m.get('channel',{}).get('name','').lower()
        if channel == 'lore':
            title = m.get('content','').split('\n',1)[0][:50].replace(' ', '_')
            with open(os.path.join(WORLD_DIR, f"{title}.json"), 'w', encoding='utf-8') as f:
                json.dump({'id': m.get('id'),
                           'title': title,
                           'content': m.get('content',''),
                           'timestamp': m.get('timestamp')}, f, indent=2)

@app.on_event("startup")
def startup_ingest():
    if os.path.exists(EXPORT_FILE):
        with open(EXPORT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        run_ingest(data)

@app.get("/")
async def root():
    return {"message": "RAG Ingestion Service: ready. Use /ask or POST /ingest."}

@app.post("/ingest")
async def ingest_export(file: UploadFile = File(...)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files allowed.")
    data = json.loads(await file.read())
    run_ingest(data)
    return {"status":"success","characters":len(os.listdir(CHAR_DIR)),
            "sessions":len(os.listdir(SESSION_DIR)),
            "world_entries":len(os.listdir(WORLD_DIR))}

@app.get("/characters")
async def list_characters():
    return os.listdir(CHAR_DIR)

@app.get("/sessions")
async def list_sessions():
    return os.listdir(SESSION_DIR)

@app.get("/world_data")
async def list_world():
    return os.listdir(WORLD_DIR)

@app.get("/ask")
async def ask(q: str):
    clean_q = q.lower().strip()
    clean_q = clean_q.translate(str.maketrans('', '', string.punctuation))
    results = []
    # Search characters
    for fname in os.listdir(CHAR_DIR):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(CHAR_DIR, fname), 'r', encoding='utf-8'))
        text = data.get('sheet','').lower().translate(str.maketrans('', '', string.punctuation))
        if clean_q in text:
            results.append({'type':'character','file':fname})
    # Search sessions
    for fname in os.listdir(SESSION_DIR):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(SESSION_DIR, fname), 'r', encoding='utf-8'))
        text = ' '.join(e.get('text','') for e in data.get('entries',[])).lower()
        text = text.translate(str.maketrans('','',string.punctuation))
        if clean_q in text:
            results.append({'type':'session','file':fname})
    # Search world
    for fname in os.listdir(WORLD_DIR):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(WORLD_DIR, fname), 'r', encoding='utf-8'))
        text = data.get('content','').lower().translate(str.maketrans('','',string.punctuation))
        if clean_q in text:
            results.append({'type':'world','file':fname})
    return {'query':q,'results':results}
