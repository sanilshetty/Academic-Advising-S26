"""
FastAPI backend for the Purdue CS CODO Eligibility Advisor.
Wraps rag_pipeline.py and ingest.py — those files are unchanged.

Start with:
    uvicorn server:app --reload --port 8000
"""

import os
import time
import shutil
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# Startup: warm up the RAG chain once so the first chat request is fast
# ---------------------------------------------------------------------------
rag_chain = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_chain
    db_path = "data/vectordb"
    if os.path.exists(db_path):
        try:
            from rag_pipeline import get_rag_chain
            rag_chain = get_rag_chain()
            print("✅ RAG chain loaded successfully.")
        except Exception as e:
            print(f"⚠️  RAG chain failed to load: {e}")
    else:
        print("⚠️  Vector DB not found. Run ingest first.")
    yield
    # Cleanup (nothing needed)


app = FastAPI(title="CODO Advisor API", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server (port 5173) and any localhost origin
# ---------------------------------------------------------------------------
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    transcript_data: str = "No transcript provided."
    chat_history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    answer: str
    latency_ms: float

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/status")
def get_status():
    """Check whether the vector database is ready."""
    db_ready = os.path.exists("data/vectordb")
    return {"db_ready": db_ready}


@app.post("/ingest")
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Accept one or more PDF / TXT files, save them to data/raw_data/,
    then rebuild the vector database.
    """
    save_dir = "data/raw_data"
    os.makedirs(save_dir, exist_ok=True)

    saved = []
    for f in files:
        dest = os.path.join(save_dir, f.filename)
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved.append(f.filename)

    try:
        from ingest import create_vector_db
        result = create_vector_db(reset=True)

        # Reload the RAG chain so subsequent /chat calls use the new DB
        global rag_chain
        from rag_pipeline import get_rag_chain
        rag_chain = get_rag_chain()

        return {"message": result, "files_saved": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Run the RAG pipeline for a single turn.
    Accepts the full chat history so the chain can contextualize follow-ups.
    """
    global rag_chain

    if rag_chain is None:
        # Attempt lazy init if DB appeared since startup
        if not os.path.exists("data/vectordb"):
            raise HTTPException(
                status_code=503,
                detail="Vector database not found. Please upload and ingest documents first."
            )
        try:
            from rag_pipeline import get_rag_chain
            rag_chain = get_rag_chain()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load RAG chain: {e}")

    # Convert chat history to LangChain message objects
    from langchain_core.messages import HumanMessage, AIMessage
    lc_history = []
    for msg in req.chat_history:
        if msg.role == "user":
            lc_history.append(HumanMessage(content=msg.content))
        else:
            lc_history.append(AIMessage(content=msg.content))

    try:
        transcript_len = len(req.transcript_data)
        print("\n" + "="*60)
        print(f"[TRANSCRIPT VERIFICATION] length: {transcript_len} chars")
        print("Below is the exact transcript text being sent to the AI:")
        print("-" * 60)
        print(req.transcript_data)
        print("="*60 + "\n")
        start = time.time()
        answer = rag_chain.invoke({
            "chat_history": lc_history,
            "question": req.question,
            "transcript_data": req.transcript_data,
        })
        elapsed_ms = (time.time() - start) * 1000

        return ChatResponse(answer=answer, latency_ms=round(elapsed_ms, 1))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# Serve React Frontend (Dynamic static mounting for Hugging Face Spaces Docker)
# ---------------------------------------------------------------------------
frontend_dist = "frontend/dist"
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=f"{frontend_dist}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        html_path = os.path.join(frontend_dist, "index.html")

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html for client-side routing
        return FileResponse(html_path)
