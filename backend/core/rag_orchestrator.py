"""
RAG Orchestrator: Coordinates all 4 phases of the multi-modal RAG system.
"""

import os
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from pathlib import Path
import aiofiles
import json

from .phase1_document_decomposition import DocumentDecomposer, DocumentChunk, VisualElement
from .phase2_representation import MultiModalEmbedder, SyntheticDocument
from .phase3_query_processing import QueryProcessor, QueryAnalysis
from .phase4_retrieval_generation import AdvancedRetriever, GeneratedResponse

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """
    Main orchestrator for the 4-phase RAG system.
    Coordinates document processing, embedding, query processing, and response generation.
    """
    
    def __init__(self, upload_dir: str = "/tmp/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.document_decomposer = DocumentDecomposer()
        self.embedder = MultiModalEmbedder()
        self.query_processor = QueryProcessor()
        self.retriever = AdvancedRetriever(self.embedder, self.query_processor)
        
        # Document registry
        self.document_registry = {}
        self.processing_status = {}
        
        logger.info("RAG Orchestrator initialized successfully")
    
    async def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a document through all phases of the RAG pipeline.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            
        Returns:
            Dict containing processing results and document metadata
        """
        document_id = str(uuid.uuid4())
        logger.info(f"Starting document processing for {filename} (ID: {document_id})")
        
        try:
            # Update processing status
            self.processing_status[document_id] = {
                'status': 'processing',
                'phase': 'saving_file',
                'progress': 0,
                'start_time': datetime.utcnow().isoformat()
            }
            
            # Save file to disk
            file_path = self.upload_dir / f"{document_id}_{filename}"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Phase 1: Document Decomposition
            logger.info(f"Phase 1: Decomposing document {document_id}")
            self.processing_status[document_id].update({
                'phase': 'decomposition',
                'progress': 25
            })
            
            text_chunks, visual_elements = self.document_decomposer.decompose_document(
                str(file_path), document_id
            )
            
            # Phase 2: Multi-Modal Embedding
            logger.info(f"Phase 2: Creating embeddings for document {document_id}")
            self.processing_status[document_id].update({
                'phase': 'embedding',
                'progress': 50
            })
            
            # Create synthetic documents from visuals
            synthetic_docs = self.embedder.create_synthetic_documents(visual_elements)
            
            # Create embeddings
            enriched_vectors = self.embedder.embed_documents(text_chunks, synthetic_docs)
            
            # Store vectors
            self.embedder.store_vectors(enriched_vectors)
            
            # Phase 3: Store metadata for retrieval
            logger.info(f"Phase 3: Storing metadata for document {document_id}")
            self.processing_status[document_id].update({
                'phase': 'metadata_storage',
                'progress': 75
            })
            
            # Store visual elements for retrieval
            for visual in visual_elements:
                self.retriever.add_visual_element(visual.id, {
                    'type': visual.type,
                    'page_number': visual.page_number,
                    'image_data': visual.image_data,
                    'description': visual.description or '',
                    'bbox': visual.bbox
                })
            
            # Store document metadata
            document_metadata = {
                'id': document_id,
                'filename': filename,
                'processing_time': datetime.utcnow().isoformat(),
                'text_chunks': len(text_chunks),
                'visual_elements': len(visual_elements),
                'synthetic_documents': len(synthetic_docs),
                'total_vectors': len(enriched_vectors)
            }
            
            self.document_registry[document_id] = document_metadata
            self.retriever.add_document_metadata(document_id, document_metadata)
            
            # Complete processing
            self.processing_status[document_id].update({
                'status': 'completed',
                'phase': 'completed',
                'progress': 100,
                'end_time': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Successfully processed document {document_id}")
            
            return {
                'document_id': document_id,
                'status': 'success',
                'metadata': document_metadata,
                'processing_stats': {
                    'text_chunks': len(text_chunks),
                    'visual_elements': len(visual_elements),
                    'synthetic_documents': len(synthetic_docs),
                    'total_vectors': len(enriched_vectors)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Update error status
            self.processing_status[document_id].update({
                'status': 'error',
                'error': str(e),
                'end_time': datetime.utcnow().isoformat()
            })
            
            return {
                'document_id': document_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def query_documents(self, query: str, document_id: str = None, 
                             conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Query the processed documents using the 4-phase pipeline.
        
        Args:
            query: User query
            document_id: Optional specific document to query
            conversation_history: Previous conversation context
            
        Returns:
            Dict containing the generated response and metadata
        """
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Check if we have any processed documents
            if not self.document_registry:
                return {
                    'status': 'error',
                    'error': 'No documents have been processed yet. Please upload and process a document first.'
                }
            
            # Use Phase 4 for retrieval and generation
            response = self.retriever.retrieve_and_generate(
                query, document_id, conversation_history
            )
            
            logger.info(f"Generated response with confidence: {response.confidence_score}")
            
            return {
                'status': 'success',
                'response': response.content,
                'sources': response.sources,
                'visuals': response.visuals,
                'confidence_score': response.confidence_score,
                'response_type': response.response_type,
                'metadata': response.metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get processing status for a document."""
        if document_id in self.processing_status:
            return self.processing_status[document_id]
        elif document_id in self.document_registry:
            return {'status': 'completed', 'progress': 100}
        else:
            return {'status': 'not_found'}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            'total_documents': len(self.document_registry),
            'processing_documents': len([
                s for s in self.processing_status.values() 
                if s['status'] == 'processing'
            ]),
            'vector_stats': self.embedder.get_vector_stats(),
            'system_components': {
                'document_decomposer': 'active',
                'embedder': 'active',
                'query_processor': 'active',
                'retriever': 'active'
            }
        }
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get list of all processed documents."""
        documents = []
        for doc_id, metadata in self.document_registry.items():
            doc_info = metadata.copy()
            doc_info['status'] = self.get_document_status(doc_id)
            documents.append(doc_info)
        return documents
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document and its associated data."""
        try:
            if document_id in self.document_registry:
                # Remove from registry
                del self.document_registry[document_id]
                
                # Remove from processing status
                if document_id in self.processing_status:
                    del self.processing_status[document_id]
                
                # Clean up file
                for file_path in self.upload_dir.glob(f"{document_id}_*"):
                    file_path.unlink()
                
                logger.info(f"Deleted document {document_id}")
                return {'status': 'success', 'message': 'Document deleted successfully'}
            else:
                return {'status': 'error', 'error': 'Document not found'}
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def cleanup_expired_documents(self, max_age_hours: int = 24):
        """Clean up old documents and processing statuses."""
        try:
            current_time = datetime.utcnow()
            expired_docs = []
            
            for doc_id, metadata in self.document_registry.items():
                processing_time = datetime.fromisoformat(metadata['processing_time'])
                age_hours = (current_time - processing_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    expired_docs.append(doc_id)
            
            for doc_id in expired_docs:
                self.delete_document(doc_id)
            
            logger.info(f"Cleaned up {len(expired_docs)} expired documents")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired documents: {str(e)}")
    
    async def test_system(self) -> Dict[str, Any]:
        """Test the complete system functionality."""
        try:
            # Test document decomposer
            decomposer_test = hasattr(self.document_decomposer, 'decompose_document')
            
            # Test embedder
            embedder_test = hasattr(self.embedder, 'embed_documents')
            
            # Test query processor
            query_processor_test = hasattr(self.query_processor, 'analyze_query')
            
            # Test retriever
            retriever_test = hasattr(self.retriever, 'retrieve_and_generate')
            
            # Test vector store
            vector_store_test = self.embedder.vector_index is not None
            
            all_tests_passed = all([
                decomposer_test, embedder_test, query_processor_test, 
                retriever_test, vector_store_test
            ])
            
            return {
                'status': 'success' if all_tests_passed else 'partial',
                'tests': {
                    'document_decomposer': decomposer_test,
                    'embedder': embedder_test,
                    'query_processor': query_processor_test,
                    'retriever': retriever_test,
                    'vector_store': vector_store_test
                },
                'system_stats': self.get_system_stats()
            }
            
        except Exception as e:
            logger.error(f"Error testing system: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }