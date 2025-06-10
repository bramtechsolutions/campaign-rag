import json
import os
from typing import List, Dict

# Paths
BASE_DIR = os.path.dirname(__file__)
EXPORT_PATH = os.path.join(BASE_DIR, 'in-game_export.json')
CHAR_DIR = os.path.join(BASE_DIR, 'characters')
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
WORLD_DIR = os.path.join(BASE_DIR, 'world_data')

# Ensure directories exist
for d in (CHAR_DIR, SESSION_DIR, WORLD_DIR):
    os.makedirs(d, exist_ok=True)

def load_export(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path: str, data: Dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_characters(messages: List[Dict]) -> None:
    for m in messages:
        if m.get('type') == 'character_definition':
            name = m['author']['name'].replace(' ', '_')
            filename = os.path.join(CHAR_DIR, f"{name}.json")
            character = {
                'id': m['id'],
                'name': m['author']['name'],
                'sheet': m.get('content'),
                'timestamp': m['timestamp']
            }
            write_json(filename, character)

def extract_sessions(messages: List[Dict]) -> None:
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
        filename = os.path.join(SESSION_DIR, f"session_{date}.json")
        write_json(filename, {'session_date': date, 'entries': entries})

def extract_world_data(messages: List[Dict]) -> None:
    for m in messages:
        if m.get('channel_type') == 'lore':
            title = m.get('content', '').split('\n',1)[0][:50].replace(' ', '_')
            filename = os.path.join(WORLD_DIR, f"{title}.json")
            entry = {
                'id': m['id'],
                'title': title,
                'content': m.get('content'),
                'timestamp': m['timestamp']
            }
            write_json(filename, entry)

def main():
    export = load_export(EXPORT_PATH)
    messages = export.get('messages', [])

    extract_characters(messages)
    extract_sessions(messages)
    extract_world_data(messages)

    print("Export complete:")
    print(f"- Characters in {CHAR_DIR}")
    print(f"- Sessions in {SESSION_DIR}")
    print(f"- World data in {WORLD_DIR}")

if __name__ == '__main__':
    main()
