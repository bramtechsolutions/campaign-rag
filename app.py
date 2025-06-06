from fastapi import FastAPI, Request
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings  # ✅ NEW SETTINGS API
)
from llama_index.llms.openai import OpenAI
import os

app = FastAPI()

# Load OpenAI API key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=openai_api_key)

# Apply the LLM to global settings (new way)
Settings.llm = llm

PERSIST_DIR = "./storage"

try:
    # Try to load the index from storage
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)
except Exception:
    # If loading fails, rebuild from scratch
    documents = SimpleDirectoryReader("documents").load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)

# Set up the query engine
query_engine = index.as_query_engine()

@app.get("/")
async def root():
    return {"message": "Campaign RAG is running."}

@app.get("/ask")
async def ask(request: Request):
    query = request.query_params.get("q")
    if not query:
        return {"error": "Missing 'q' parameter"}
    response = query_engine.query(query)
    return {"response": str(response)}
