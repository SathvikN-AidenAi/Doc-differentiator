import io
import json
from pypdf import PdfReader
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from app.diff import compare_documents



app = FastAPI(title="DocDiff Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Maintain document content + chat memory
chat_history = []

doc_cache = {"before_text": "", "after_text": ""}

@app.post("/compare")
async def compare_docs(before_file: UploadFile = File(...), after_file: UploadFile = File(...)):
    """
    Compare two uploaded PDFs and extract their text for later LLM analysis.
    """
    before_bytes = await before_file.read()
    after_bytes = await after_file.read()

    # ✅ wrap bytes in BytesIO to make them seekable
    before_reader = PdfReader(io.BytesIO(before_bytes))
    after_reader = PdfReader(io.BytesIO(after_bytes))

    before_text = "\n".join([p.extract_text() or "" for p in before_reader.pages])
    after_text = "\n".join([p.extract_text() or "" for p in after_reader.pages])

    # cache the extracted text for LLM
    doc_cache["before_text"] = before_text
    doc_cache["after_text"] = after_text

    # now run your actual diff logic
    result = await compare_documents(before_bytes, after_bytes, before_file.filename, after_file.filename)
    return result

@app.post("/ask")
async def ask_llm(question: str = Form(...), diffs: str = Form(...)):
    """
    Streams conversational responses from Ollama in real time.
    """
    payload = {
        "model": "llama3.2",  # or any other Llama model you’ve pulled locally
        "prompt": (
            "You are DocDiff Assistant — a friendly AI that explains document differences conversationally. "
            "Use natural language, respond quickly, and keep it concise.\n\n"
            f"User Question: {question}\n\n"
            f"Document Differences:\n{diffs}\n\n"
            "If the question is unrelated to the diffs, just chat naturally.\n\n"
        ),
        "stream": True,
    }

    async def stream_llama():
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:11434/api/generate", json=payload) as resp:
                async for line in resp.content:
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            text = data.get("response", "")
                            if text:
                                yield text
                        except json.JSONDecodeError:
                            continue

    return StreamingResponse(stream_llama(), media_type="text/plain")
