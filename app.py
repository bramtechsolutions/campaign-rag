from fastapi import FastAPI, Request
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    ServiceContext,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.openai import OpenAI  # ✅ FIXED IMPORT FOR LATEST VERSIONS
import os

app = FastAPI()

# Load your OpenAI API key from Render environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=openai_api_key)

# Create a service context with the selected LLM
service_context = ServiceContext.from_defaults(llm=llm)

# Set your persistent index directory (created automatically after first run)
PERSIST_DIR = "./storage"

try:
    # Try to load existing index from disk
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context, service_context=service_context)
except Exception:
    # If no index exists yet, build from documents
    documents = SimpleDirectoryReader("documents").load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    index.storage_context.persist(persist_dir=PERSIST_DIR)

# Create a query engine to allow API access
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
