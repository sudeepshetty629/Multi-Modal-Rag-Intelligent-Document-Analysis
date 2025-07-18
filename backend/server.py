from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import google.generativeai as genai
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import uuid

load_dotenv()

# Global variables for database and AI clients
mongodb_client = None
database = None
genai_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client, database, genai_client
    
    # Initialize MongoDB
    mongodb_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    database = mongodb_client.multimodal_rag
    
    # Initialize Google Gemini
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    genai_client = genai.GenerativeModel('gemini-1.5-pro')
    
    print("🚀 Multi-Modal RAG System Started!")
    print(f"📊 Database: {database.name}")
    print(f"🤖 AI Model: Gemini 1.5 Pro")
    
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()

app = FastAPI(
    title="Multi-Modal RAG System",
    description="Advanced 4-Phase Intelligent Pipeline for Document Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "connected" if mongodb_client else "disconnected",
            "ai_model": "ready" if genai_client else "not_ready"
        }
    }

# Test endpoint for AI model
@app.get("/api/test-ai")
async def test_ai():
    try:
        response = genai_client.generate_content("Hello, this is a test message. Please respond with 'AI system is working!'")
        return {
            "status": "success",
            "model": "gemini-1.5-pro",
            "response": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")

# Document upload endpoint
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Create document record
        document = {
            "id": doc_id,
            "filename": file.filename,
            "upload_time": datetime.utcnow(),
            "status": "uploaded",
            "processing_status": "pending",
            "file_size": file.size,
            "content_type": file.content_type
        }
        
        # Store document metadata
        await database.documents.insert_one(document)
        
        # Save file content (you'll implement file storage logic)
        file_content = await file.read()
        
        # TODO: Implement PDF processing pipeline
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": file.filename,
            "message": "Document uploaded successfully. Processing will begin shortly."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

# Get documents list
@app.get("/api/documents")
async def get_documents():
    try:
        documents = await database.documents.find({}).to_list(length=100)
        return {
            "status": "success",
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Query endpoint
@app.post("/api/query")
async def query_documents(query_data: Dict[str, Any]):
    try:
        query = query_data.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # TODO: Implement 4-phase pipeline
        # Phase 1: Query Analysis
        # Phase 2: Retrieval
        # Phase 3: Template Selection
        # Phase 4: Response Generation
        
        # Temporary response
        response = await genai_client.generate_content(f"Please answer this query: {query}")
        
        return {
            "status": "success",
            "query": query,
            "response": response.text,
            "sources": [],
            "visuals": []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)