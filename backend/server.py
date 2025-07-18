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
import logging

# Import RAG components
from core.rag_orchestrator import RAGOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Global variables for database and AI clients
mongodb_client = None
database = None
genai_client = None
rag_orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client, database, genai_client, rag_orchestrator
    
    # Initialize MongoDB
    mongodb_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    database = mongodb_client.multimodal_rag
    
    # Initialize Google Gemini
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    genai_client = genai.GenerativeModel('gemini-1.5-pro')
    
    # Initialize RAG Orchestrator
    rag_orchestrator = RAGOrchestrator()
    
    print("🚀 Multi-Modal RAG System Started!")
    print(f"📊 Database: {database.name}")
    print(f"🤖 AI Model: Gemini 1.5 Pro")
    print(f"🔄 RAG Orchestrator: Initialized")
    
    # Test the system
    system_test = await rag_orchestrator.test_system()
    print(f"🧪 System Test: {system_test['status']}")
    
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
            "ai_model": "ready" if genai_client else "not_ready",
            "rag_orchestrator": "ready" if rag_orchestrator else "not_ready"
        }
    }

# System statistics endpoint
@app.get("/api/system/stats")
async def get_system_stats():
    if not rag_orchestrator:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    stats = rag_orchestrator.get_system_stats()
    return {
        "status": "success",
        "stats": stats
    }

# Test AI model endpoint
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
        if not rag_orchestrator:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        file_content = await file.read()
        
        # Check file size (50MB limit)
        if len(file_content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 50MB")
        
        # Process document through RAG pipeline
        result = await rag_orchestrator.process_document(file_content, file.filename)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Store document metadata in MongoDB
        document_record = {
            "id": result['document_id'],
            "filename": file.filename,
            "upload_time": datetime.utcnow(),
            "status": "processing",
            "processing_status": "completed",
            "file_size": len(file_content),
            "content_type": file.content_type,
            "processing_stats": result.get('processing_stats', {})
        }
        
        await database.documents.insert_one(document_record)
        
        return {
            "status": "success",
            "document_id": result['document_id'],
            "filename": file.filename,
            "message": "Document uploaded and processed successfully",
            "processing_stats": result.get('processing_stats', {})
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

# Get documents list
@app.get("/api/documents")
async def get_documents():
    try:
        if not rag_orchestrator:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        # Get documents from RAG orchestrator
        documents = rag_orchestrator.get_document_list()
        
        # Also get from MongoDB for consistency
        mongo_docs = await database.documents.find({}).to_list(length=100)
        
        return {
            "status": "success",
            "documents": mongo_docs,
            "rag_documents": documents
        }
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Get document status
@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: str):
    try:
        if not rag_orchestrator:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        status = rag_orchestrator.get_document_status(document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "processing_status": status
        }
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Main query endpoint - Enhanced with 4-phase pipeline
@app.post("/api/query")
async def query_documents(query_data: Dict[str, Any]):
    try:
        if not rag_orchestrator:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        query = query_data.get("query", "")
        document_id = query_data.get("document_id")
        conversation_history = query_data.get("conversation_history", [])
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Process query through 4-phase RAG pipeline
        result = await rag_orchestrator.query_documents(
            query, document_id, conversation_history
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        return {
            "status": "success",
            "query": query,
            "response": result['response'],
            "sources": result.get('sources', []),
            "visuals": result.get('visuals', []),
            "confidence_score": result.get('confidence_score', 0.0),
            "response_type": result.get('response_type', 'basic'),
            "metadata": result.get('metadata', {})
        }
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

# Delete document endpoint
@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    try:
        if not rag_orchestrator:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        # Delete from RAG orchestrator
        result = rag_orchestrator.delete_document(document_id)
        
        # Delete from MongoDB
        await database.documents.delete_one({"id": document_id})
        
        return {
            "status": "success",
            "message": "Document deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Test complete system endpoint
@app.get("/api/test-system")
async def test_complete_system():
    try:
        if not rag_orchestrator:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        system_test = await rag_orchestrator.test_system()
        
        return {
            "status": "success",
            "system_test": system_test
        }
        
    except Exception as e:
        logger.error(f"System test error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System test error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)