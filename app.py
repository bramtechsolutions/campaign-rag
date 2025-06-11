from fastapi import FastAPI, UploadFile, File, HTTPException
import json
import os
import string
from typing import List, Dict

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "RAG Ingestion Service: POST to /ingest or use /ask"}

BASE_DIR = os.path.dirname(__file__)
EXPORT_PATH = os.path.join(BASE_DIR, 'in-game_export.json')
CHAR_DIR = os.path.join(BASE_DIR, 'characters')
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
WORLD_DIR = os.path.join(BASE_DIR, 'world_data')

# Load or ingest data at startup
def load_data():
    with open(EXPORT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f).get('messages', [])

messages = []
if os.path.exists(EXPORT_PATH):
    messages = load_data()

def normalize(text: str) -> str:
    return text.lower().translate(str.maketrans('', '', string.punctuation))

@app.get("/ask")
async def ask(q: str):
    # Tokenize the query into keywords
    tokens = [t for t in normalize(q).split() if len(t) > 2]
    results = []

    for m in messages:
        content = m.get('content', '')
        norm = normalize(content)
        # Check if all tokens are present
        if all(tok in norm for tok in tokens):
            results.append({
                'id': m.get('id'),
                'author': m.get('author', {}).get('name'),
                'content': content,
                'timestamp': m.get('timestamp')
            })

    return {'query': q, 'matches': results}
