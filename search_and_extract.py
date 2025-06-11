#!/usr/bin/env python3
import json
import re
import string
import sys
import os

# Load messages
EXPORT_PATH = os.path.join(os.path.dirname(__file__), 'in-game_export.json')
with open(EXPORT_PATH, encoding='utf-8') as f:
    messages = json.load(f).get('messages', [])

STOPWORDS = set([
    'what','is','are','the','a','an','of','and','to','in','on',
    'his','her','he','she','its','color','instrument','playing'
])

def normalize(text):
    return text.lower().translate(str.maketrans('', '', string.punctuation))

def extract_eye_color(text):
    m = re.search(r'(\w+)\s+eyes', text, re.IGNORECASE)
    return m.group(1) if m else None

def extract_instrument(text):
    instruments = ['viol', 'lute', 'violin', 'flute', 'harp', 'fiddle', 'guitar', 'drum', 'strings']
    low = text.lower()
    for inst in instruments:
        if inst in low:
            return inst
    return None

def answer_query(query):
    # Tokenize and filter
    tokens = [t for t in normalize(query).split() if t not in STOPWORDS]
    results = []
    for m in messages:
        content = m.get('content','')
        if not content:
            continue
        norm = normalize(content)
        if all(tok in norm for tok in tokens):
            # Extraction logic
            if 'eyes' in normalize(query):
                color = extract_eye_color(content)
                return {'query': query, 'answer': color, 'source': content.strip()}
            if 'instrument' in normalize(query):
                inst = extract_instrument(content)
                return {'query': query, 'answer': inst, 'source': content.strip()}
            # default
            return {'query': query, 'answer': content.strip()}
    return {'query': query, 'answer': None}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 search_and_extract.py "your query here"')
        sys.exit(1)
    result = answer_query(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
