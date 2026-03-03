from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
from pathlib import Path

from backend.app.config import config
from backend.app.simple_qa import SimpleContractQA

app = FastAPI(title="Simple Contract Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global QA instance
qa_system = SimpleContractQA()

# Models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[dict]

class UploadResponse(BaseModel):
    message: str
    pages: int
    filename: str

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    file_path = config.UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        result = qa_system.load_pdf(str(file_path))
        return UploadResponse(
            message="PDF loaded successfully",
            pages=result["pages"],
            filename=result["filename"]
        )
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        file_path.unlink(missing_ok=True)

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        result = qa_system.ask(request.question)
        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/summary")
async def get_summary():
    try:
        summary = qa_system.get_summary()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
