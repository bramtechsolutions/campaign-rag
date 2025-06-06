from fastapi import FastAPI, Request
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, ServiceContext, StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
import os
import logging

app = FastAPI()

# Logging (optional)
logging.basicConfig(level=logging.INFO)

# Load OpenAI key
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=openai_api_key)

# Use service context
service_context = ServiceContext.from_defaults(llm=llm)

# Load index from persistent storage if it exists
PERSIST_DIR = "./storage"
try:
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context, service_context=service_context)
except Exception:
    # First time: Load documents and create index
    documents = SimpleDirectoryReader("documents").load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    index.storage_context.persist(persist_dir=PERSIST_DIR)

# Create query engine
query_engine = index.as_query_engine()

@app.get("/")
async def root():
    return {"message": "LlamaIndex RAG is running."}

@app.get("/ask")
async def ask(request: Request):
    query = request.query_params.get("q")
    if not query:
        return {"error": "Missing 'q' parameter"}
    response = query_engine.query(query)
    return {"response": str(response)}
