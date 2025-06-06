from fastapi import FastAPI, Request
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms import OpenAI
import os

app = FastAPI()

# Load environment variable for OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=openai_api_key)
service_context = ServiceContext.from_defaults(llm=llm)

# Load and index documents
documents = SimpleDirectoryReader("documents").load_data()
index = VectorStoreIndex.from_documents(documents, service_context=service_context)
query_engine = index.as_query_engine()

@app.get("/")
async def root():
    return {"message": "LlamaIndex campaign RAG is running."}

@app.get("/ask")
async def ask(request: Request):
    q = request.query_params.get("q")
    if not q:
        return {"error": "Query param 'q' is required."}
    response = query_engine.query(q)
    return {"response": str(response)}
