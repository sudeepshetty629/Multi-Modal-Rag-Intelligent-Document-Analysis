"""
Phase 2: Representation & Multi-Modal Embedding
This phase transforms decomposed elements into a unified, searchable format.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
import google.generativeai as genai
from .phase1_document_decomposition import DocumentChunk, VisualElement
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class SyntheticDocument:
    """Represents a synthetic document created from visual elements."""
    id: str
    content: str
    original_visual_id: str
    description: str
    extracted_text: str
    caption: str
    context: str
    metadata: Dict[str, Any]

@dataclass
class EnrichedVector:
    """Represents an enriched vector with metadata."""
    id: str
    vector: np.ndarray
    content: str
    content_type: str
    metadata: Dict[str, Any]
    visual_link: Optional[str] = None

class MultiModalEmbedder:
    """Handles multi-modal embedding and representation."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.vector_index = None
        self.document_store = {}
        
    def initialize_vector_store(self):
        """Initialize FAISS vector store."""
        self.vector_index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product similarity
        logger.info(f"Initialized FAISS index with dimension {self.embedding_dim}")
    
    def create_synthetic_documents(self, visual_elements: List[VisualElement]) -> List[SyntheticDocument]:
        """Create synthetic documents from visual elements."""
        synthetic_docs = []
        
        for visual in visual_elements:
            try:
                # Generate description using AI
                description = self._generate_visual_description(visual)
                
                # Extract text from visual if possible
                extracted_text = self._extract_text_from_visual(visual)
                
                # Create synthetic document
                synthetic_content = self._create_synthetic_content(
                    visual, description, extracted_text
                )
                
                synthetic_doc = SyntheticDocument(
                    id=f"synthetic_{visual.id}",
                    content=synthetic_content,
                    original_visual_id=visual.id,
                    description=description,
                    extracted_text=extracted_text,
                    caption=visual.caption or "",
                    context=self._get_visual_context(visual),
                    metadata={
                        'visual_type': visual.type,
                        'page_number': visual.page_number,
                        'bbox': visual.bbox,
                        'creation_method': 'ai_generated'
                    }
                )
                
                synthetic_docs.append(synthetic_doc)
                
            except Exception as e:
                logger.error(f"Error creating synthetic document for {visual.id}: {str(e)}")
                continue
                
        return synthetic_docs
    
    def embed_documents(self, text_chunks: List[DocumentChunk], 
                       synthetic_docs: List[SyntheticDocument]) -> List[EnrichedVector]:
        """Create embeddings for all documents."""
        enriched_vectors = []
        
        # Embed text chunks
        for chunk in text_chunks:
            try:
                vector = self.embedding_model.encode(chunk.content)
                enriched_vector = EnrichedVector(
                    id=chunk.id,
                    vector=vector,
                    content=chunk.content,
                    content_type=chunk.content_type,
                    metadata=chunk.metadata,
                    visual_link=chunk.visual_link
                )
                enriched_vectors.append(enriched_vector)
            except Exception as e:
                logger.error(f"Error embedding chunk {chunk.id}: {str(e)}")
                continue
        
        # Embed synthetic documents
        for synthetic in synthetic_docs:
            try:
                vector = self.embedding_model.encode(synthetic.content)
                enriched_vector = EnrichedVector(
                    id=synthetic.id,
                    vector=vector,
                    content=synthetic.content,
                    content_type='synthetic_visual',
                    metadata=synthetic.metadata,
                    visual_link=synthetic.original_visual_id
                )
                enriched_vectors.append(enriched_vector)
            except Exception as e:
                logger.error(f"Error embedding synthetic document {synthetic.id}: {str(e)}")
                continue
        
        return enriched_vectors
    
    def store_vectors(self, enriched_vectors: List[EnrichedVector]):
        """Store vectors in FAISS index."""
        if self.vector_index is None:
            self.initialize_vector_store()
        
        # Prepare vectors for FAISS
        vectors_array = np.array([vec.vector for vec in enriched_vectors]).astype('float32')
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors_array)
        
        # Add to index
        self.vector_index.add(vectors_array)
        
        # Store metadata
        for i, vec in enumerate(enriched_vectors):
            self.document_store[i] = {
                'id': vec.id,
                'content': vec.content,
                'content_type': vec.content_type,
                'metadata': vec.metadata,
                'visual_link': vec.visual_link
            }
        
        logger.info(f"Stored {len(enriched_vectors)} vectors in FAISS index")
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.vector_index is None:
            raise ValueError("Vector store not initialized")
        
        # Embed query
        query_vector = self.embedding_model.encode([query]).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self.vector_index.search(query_vector, top_k)
        
        # Retrieve results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx in self.document_store:
                result = self.document_store[idx].copy()
                result['similarity_score'] = float(score)
                result['rank'] = i + 1
                results.append(result)
        
        return results
    
    def _generate_visual_description(self, visual: VisualElement) -> str:
        """Generate description for visual element using AI."""
        try:
            # Use Gemini to describe the visual
            prompt = f"""
            Analyze this {visual.type} from a document and provide a detailed description.
            
            Visual Type: {visual.type}
            Page Number: {visual.page_number + 1}
            Caption: {visual.caption or 'No caption'}
            
            Please provide:
            1. A detailed description of what this visual shows
            2. Key data points or insights if it's a chart or table
            3. Any trends or patterns visible
            4. The main purpose or message of this visual
            
            Format your response as a comprehensive analysis that would help someone understand the visual without seeing it.
            """
            
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            
            return response.text if response.text else f"Visual {visual.type} on page {visual.page_number + 1}"
            
        except Exception as e:
            logger.error(f"Error generating description for {visual.id}: {str(e)}")
            return f"Visual {visual.type} on page {visual.page_number + 1}"
    
    def _extract_text_from_visual(self, visual: VisualElement) -> str:
        """Extract text from visual element."""
        # For now, return extracted text if available
        return visual.extracted_text or ""
    
    def _create_synthetic_content(self, visual: VisualElement, description: str, extracted_text: str) -> str:
        """Create synthetic content combining all visual information."""
        content_parts = []
        
        # Add description
        if description:
            content_parts.append(f"Description: {description}")
        
        # Add extracted text
        if extracted_text:
            content_parts.append(f"Text content: {extracted_text}")
        
        # Add caption
        if visual.caption:
            content_parts.append(f"Caption: {visual.caption}")
        
        # Add context
        context = self._get_visual_context(visual)
        if context:
            content_parts.append(f"Context: {context}")
        
        # Add metadata
        content_parts.append(f"Visual type: {visual.type}")
        content_parts.append(f"Page: {visual.page_number + 1}")
        
        return "\n".join(content_parts)
    
    def _get_visual_context(self, visual: VisualElement) -> str:
        """Get context around the visual element."""
        # In a real implementation, this would analyze surrounding text
        return f"Visual element located on page {visual.page_number + 1}"
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if self.vector_index is None:
            return {"status": "not_initialized"}
        
        return {
            "total_vectors": self.vector_index.ntotal,
            "embedding_dimension": self.embedding_dim,
            "index_type": "FAISS_IndexFlatIP",
            "content_types": self._get_content_type_distribution()
        }
    
    def _get_content_type_distribution(self) -> Dict[str, int]:
        """Get distribution of content types in the store."""
        distribution = {}
        for doc in self.document_store.values():
            content_type = doc.get('content_type', 'unknown')
            distribution[content_type] = distribution.get(content_type, 0) + 1
        return distribution