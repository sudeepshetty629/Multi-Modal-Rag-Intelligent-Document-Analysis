"""
Phase 4: Advanced Retrieval & Structured Response Generation
This phase executes multi-stage retrieval and generates structured responses.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
import google.generativeai as genai
from .phase2_representation import MultiModalEmbedder
from .phase3_query_processing import QueryProcessor, QueryAnalysis, ResponseTemplate
import json

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Results from retrieval process."""
    primary_results: List[Dict[str, Any]]
    visual_results: List[Dict[str, Any]]
    context_results: List[Dict[str, Any]]
    reranked_results: List[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any]

@dataclass
class GeneratedResponse:
    """Generated response with metadata."""
    content: str
    sources: List[Dict[str, Any]]
    visuals: List[Dict[str, Any]]
    confidence_score: float
    response_type: str
    metadata: Dict[str, Any]

class AdvancedRetriever:
    """Handles multi-stage retrieval and response generation."""
    
    def __init__(self, embedder: MultiModalEmbedder, query_processor: QueryProcessor):
        self.embedder = embedder
        self.query_processor = query_processor
        self.visual_store = {}  # Store visual elements by ID
        self.document_store = {}  # Store document metadata
        
    def retrieve_and_generate(self, query: str, document_id: str = None, 
                             conversation_history: List[Dict] = None) -> GeneratedResponse:
        """Main method for retrieval and generation."""
        try:
            # Step 1: Analyze query
            analysis = self.query_processor.analyze_query(query, conversation_history)
            
            # Step 2: Multi-stage retrieval
            retrieval_results = self._multi_stage_retrieval(query, analysis, document_id)
            
            # Step 3: Select template
            template = self.query_processor.select_response_template(analysis)
            
            # Step 4: Generate response
            response = self._generate_structured_response(
                query, analysis, template, retrieval_results
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in retrieve_and_generate: {str(e)}")
            # Return error response
            return GeneratedResponse(
                content="I apologize, but I encountered an error processing your request. Please try again.",
                sources=[],
                visuals=[],
                confidence_score=0.0,
                response_type="error",
                metadata={"error": str(e)}
            )
    
    def _multi_stage_retrieval(self, query: str, analysis: QueryAnalysis, 
                              document_id: str = None) -> RetrievalResult:
        """Execute multi-stage retrieval pipeline."""
        
        # Stage 1: Primary retrieval using vector similarity
        primary_results = self._primary_retrieval(query, top_k=10)
        
        # Stage 2: Visual content retrieval if needed
        visual_results = []
        if analysis.requires_visuals:
            visual_results = self._visual_retrieval(query, analysis.visual_keywords)
        
        # Stage 3: Context expansion
        context_results = self._context_expansion(primary_results, visual_results)
        
        # Stage 4: Relevance re-ranking
        reranked_results = self._rerank_results(
            query, analysis, primary_results + visual_results + context_results
        )
        
        return RetrievalResult(
            primary_results=primary_results,
            visual_results=visual_results,
            context_results=context_results,
            reranked_results=reranked_results,
            retrieval_metadata={
                'total_retrieved': len(reranked_results),
                'visual_count': len(visual_results),
                'primary_count': len(primary_results),
                'context_count': len(context_results)
            }
        )
    
    def _primary_retrieval(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Primary vector similarity search."""
        try:
            results = self.embedder.search_similar(query, top_k)
            return results
        except Exception as e:
            logger.error(f"Error in primary retrieval: {str(e)}")
            return []
    
    def _visual_retrieval(self, query: str, visual_keywords: List[str]) -> List[Dict[str, Any]]:
        """Retrieve visual content based on query intent."""
        visual_results = []
        
        # Search for visual-related content
        visual_query = " ".join(visual_keywords + ["chart", "graph", "table", "figure"])
        results = self.embedder.search_similar(visual_query, top_k=5)
        
        # Filter for visual content
        for result in results:
            if result.get('content_type') == 'synthetic_visual':
                visual_results.append(result)
        
        return visual_results
    
    def _context_expansion(self, primary_results: List[Dict], visual_results: List[Dict]) -> List[Dict]:
        """Expand context by retrieving related content."""
        context_results = []
        
        # Get related content from same pages
        page_numbers = set()
        for result in primary_results + visual_results:
            page_num = result.get('metadata', {}).get('page_number')
            if page_num is not None:
                page_numbers.add(page_num)
        
        # Search for additional content from same pages
        for page_num in page_numbers:
            page_query = f"page {page_num}"
            page_results = self.embedder.search_similar(page_query, top_k=3)
            
            for result in page_results:
                if result not in primary_results and result not in visual_results:
                    context_results.append(result)
        
        return context_results[:5]  # Limit context expansion
    
    def _rerank_results(self, query: str, analysis: QueryAnalysis, 
                       all_results: List[Dict]) -> List[Dict]:
        """Re-rank results based on query intent and relevance."""
        scored_results = []
        
        for result in all_results:
            score = self._calculate_relevance_score(query, analysis, result)
            result['final_score'] = score
            scored_results.append(result)
        
        # Sort by final score
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored_results[:10]  # Return top 10
    
    def _calculate_relevance_score(self, query: str, analysis: QueryAnalysis, 
                                  result: Dict) -> float:
        """Calculate relevance score for re-ranking."""
        base_score = result.get('similarity_score', 0.0)
        
        # Boost visual content if visuals are required
        if analysis.requires_visuals and result.get('content_type') == 'synthetic_visual':
            base_score += 0.2
        
        # Boost based on content type match
        if analysis.intent.value in result.get('content', '').lower():
            base_score += 0.1
        
        # Consider visual keywords
        content_lower = result.get('content', '').lower()
        visual_keyword_matches = sum(1 for keyword in analysis.visual_keywords if keyword in content_lower)
        base_score += visual_keyword_matches * 0.05
        
        return min(base_score, 1.0)
    
    def _generate_structured_response(self, query: str, analysis: QueryAnalysis, 
                                    template: ResponseTemplate, 
                                    retrieval_results: RetrievalResult) -> GeneratedResponse:
        """Generate structured response using template."""
        try:
            # Prepare context
            context = {
                'document_name': 'Uploaded Document',
                'available_visuals': retrieval_results.visual_results,
                'query_analysis': analysis
            }
            
            # Generate prompts
            system_prompt = self.query_processor.generate_system_prompt(template, context)
            user_prompt = self.query_processor.generate_user_prompt(
                template, query, retrieval_results.reranked_results[:5], context
            )
            
            # Generate response using Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Construct full prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = model.generate_content(full_prompt)
            
            # Process response
            content = response.text if response.text else "I apologize, but I couldn't generate a response."
            
            # Extract sources and visuals
            sources = self._extract_sources(retrieval_results.reranked_results)
            visuals = self._extract_visuals(retrieval_results.visual_results)
            
            # Calculate confidence
            confidence = self._calculate_response_confidence(
                analysis, retrieval_results, len(content)
            )
            
            return GeneratedResponse(
                content=content,
                sources=sources,
                visuals=visuals,
                confidence_score=confidence,
                response_type=template.response_format,
                metadata={
                    'query_intent': analysis.intent.value,
                    'template_used': template.name,
                    'retrieval_stats': retrieval_results.retrieval_metadata,
                    'response_length': len(content)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return GeneratedResponse(
                content="I apologize, but I encountered an error generating the response.",
                sources=[],
                visuals=[],
                confidence_score=0.0,
                response_type="error",
                metadata={"error": str(e)}
            )
    
    def _extract_sources(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Extract source information from results."""
        sources = []
        
        for result in results[:3]:  # Limit to top 3 sources
            source = {
                'content': result.get('content', '')[:200] + '...',
                'page': result.get('metadata', {}).get('page_number', 0) + 1,
                'type': result.get('content_type', 'text'),
                'relevance_score': result.get('final_score', 0.0)
            }
            sources.append(source)
        
        return sources
    
    def _extract_visuals(self, visual_results: List[Dict]) -> List[Dict[str, Any]]:
        """Extract visual information for response."""
        visuals = []
        
        for result in visual_results[:3]:  # Limit to top 3 visuals
            visual_id = result.get('visual_link')
            if visual_id and visual_id in self.visual_store:
                visual_data = self.visual_store[visual_id]
                visual = {
                    'id': visual_id,
                    'type': visual_data.get('type', 'image'),
                    'description': result.get('content', ''),
                    'page': result.get('metadata', {}).get('page_number', 0) + 1,
                    'image_data': visual_data.get('image_data', ''),
                    'relevance_score': result.get('final_score', 0.0)
                }
                visuals.append(visual)
        
        return visuals
    
    def _calculate_response_confidence(self, analysis: QueryAnalysis, 
                                     retrieval_results: RetrievalResult, 
                                     response_length: int) -> float:
        """Calculate confidence score for the response."""
        base_confidence = analysis.confidence
        
        # Boost confidence based on retrieval quality
        if retrieval_results.reranked_results:
            avg_score = np.mean([r.get('final_score', 0) for r in retrieval_results.reranked_results])
            base_confidence += avg_score * 0.2
        
        # Boost confidence based on response length
        if response_length > 100:
            base_confidence += 0.1
        
        # Boost confidence if visuals are provided when needed
        if analysis.requires_visuals and retrieval_results.visual_results:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def add_visual_element(self, visual_id: str, visual_data: Dict):
        """Add visual element to store."""
        self.visual_store[visual_id] = visual_data
    
    def add_document_metadata(self, document_id: str, metadata: Dict):
        """Add document metadata."""
        self.document_store[document_id] = metadata