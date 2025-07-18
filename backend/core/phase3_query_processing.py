"""
Phase 3: Intelligent Query Processing & Template Selection
This phase analyzes user queries and selects appropriate response templates.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Types of query intents."""
    VISUAL = "visual"              # Requires charts, diagrams, or visual explanations
    TEXTUAL = "textual"           # Requires detailed text explanations
    HYBRID = "hybrid"             # Needs both visual and textual information
    COMPARATIVE = "comparative"   # Needs multiple sources/visuals
    ANALYTICAL = "analytical"     # Requires deep analysis or insights
    FACTUAL = "factual"          # Simple fact-based queries
    SUMMARY = "summary"          # Summarization requests

@dataclass
class QueryAnalysis:
    """Results of query analysis."""
    intent: QueryIntent
    confidence: float
    keywords: List[str]
    visual_keywords: List[str]
    complexity_score: float
    requires_visuals: bool
    requires_analysis: bool
    suggested_template: str
    metadata: Dict[str, Any]

@dataclass
class ResponseTemplate:
    """Template for generating responses."""
    name: str
    intent_type: QueryIntent
    system_prompt: str
    user_prompt_template: str
    response_format: str
    include_visuals: bool
    include_sources: bool
    analysis_depth: str  # 'basic', 'detailed', 'comprehensive'

class QueryProcessor:
    """Handles query analysis and template selection."""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.templates = self._initialize_templates()
        self.visual_keywords = self._load_visual_keywords()
        self.analytical_keywords = self._load_analytical_keywords()
        
    def analyze_query(self, query: str, conversation_history: List[Dict] = None) -> QueryAnalysis:
        """Analyze user query to determine intent and requirements."""
        try:
            # Basic preprocessing
            query_lower = query.lower().strip()
            
            # Extract keywords
            keywords = self._extract_keywords(query)
            visual_keywords = self._extract_visual_keywords(query)
            
            # Detect intent
            intent = self._detect_intent(query, keywords, visual_keywords)
            
            # Calculate confidence
            confidence = self._calculate_confidence(query, intent, keywords)
            
            # Assess complexity
            complexity_score = self._assess_complexity(query, keywords)
            
            # Determine requirements
            requires_visuals = self._requires_visuals(intent, visual_keywords)
            requires_analysis = self._requires_analysis(intent, keywords)
            
            # Select template
            suggested_template = self._select_template(intent, complexity_score, requires_visuals)
            
            return QueryAnalysis(
                intent=intent,
                confidence=confidence,
                keywords=keywords,
                visual_keywords=visual_keywords,
                complexity_score=complexity_score,
                requires_visuals=requires_visuals,
                requires_analysis=requires_analysis,
                suggested_template=suggested_template,
                metadata={
                    'query_length': len(query),
                    'word_count': len(query.split()),
                    'has_question_words': self._has_question_words(query),
                    'is_comparative': self._is_comparative_query(query),
                    'conversation_context': len(conversation_history) if conversation_history else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            # Return default analysis
            return QueryAnalysis(
                intent=QueryIntent.TEXTUAL,
                confidence=0.5,
                keywords=[],
                visual_keywords=[],
                complexity_score=0.5,
                requires_visuals=False,
                requires_analysis=False,
                suggested_template="basic_response",
                metadata={}
            )
    
    def select_response_template(self, analysis: QueryAnalysis) -> ResponseTemplate:
        """Select appropriate response template based on analysis."""
        template_name = analysis.suggested_template
        
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            # Fallback to basic template
            return self.templates["basic_response"]
    
    def generate_system_prompt(self, template: ResponseTemplate, context: Dict[str, Any]) -> str:
        """Generate system prompt for the AI model."""
        system_prompt = template.system_prompt
        
        # Add context-specific information
        if context.get('document_name'):
            system_prompt += f"\n\nDocument being analyzed: {context['document_name']}"
        
        if context.get('available_visuals'):
            system_prompt += f"\n\nAvailable visuals: {len(context['available_visuals'])} visual elements"
        
        return system_prompt
    
    def generate_user_prompt(self, template: ResponseTemplate, query: str, 
                           retrieved_content: List[Dict], context: Dict[str, Any]) -> str:
        """Generate user prompt with retrieved content."""
        # Build content sections
        text_content = []
        visual_content = []
        
        for item in retrieved_content:
            if item.get('content_type') == 'synthetic_visual':
                visual_content.append(item)
            else:
                text_content.append(item)
        
        # Format content
        content_sections = []
        
        if text_content:
            content_sections.append("**Text Content:**")
            for i, item in enumerate(text_content[:5]):  # Limit to top 5
                content_sections.append(f"{i+1}. {item['content'][:500]}...")
        
        if visual_content and template.include_visuals:
            content_sections.append("\n**Visual Content:**")
            for i, item in enumerate(visual_content[:3]):  # Limit to top 3
                content_sections.append(f"{i+1}. {item['content'][:300]}...")
        
        # Generate prompt using template
        user_prompt = template.user_prompt_template.format(
            query=query,
            content="\n".join(content_sections),
            analysis_depth=template.analysis_depth
        )
        
        return user_prompt
    
    def _initialize_templates(self) -> Dict[str, ResponseTemplate]:
        """Initialize response templates."""
        templates = {}
        
        # Basic response template
        templates["basic_response"] = ResponseTemplate(
            name="basic_response",
            intent_type=QueryIntent.TEXTUAL,
            system_prompt="""You are an advanced AI assistant specialized in document analysis. 
            Provide accurate, helpful responses based on the document content provided. 
            Always cite sources and maintain factual accuracy.""",
            user_prompt_template="""Based on the following document content, please answer this question: {query}

Content:
{content}

Please provide a {analysis_depth} response with clear explanations and source citations.""",
            response_format="structured",
            include_visuals=False,
            include_sources=True,
            analysis_depth="detailed"
        )
        
        # Visual-focused template
        templates["visual_response"] = ResponseTemplate(
            name="visual_response",
            intent_type=QueryIntent.VISUAL,
            system_prompt="""You are an expert in visual data analysis. When analyzing charts, graphs, 
            tables, or diagrams, provide detailed descriptions of visual elements, data trends, 
            and insights. Always explain what visual elements show and their significance.""",
            user_prompt_template="""Analyze the following query about visual content: {query}

Content (including visual descriptions):
{content}

Please provide a {analysis_depth} analysis that:
1. Describes relevant visual elements in detail
2. Explains data trends and patterns
3. Provides insights and interpretations
4. Includes source citations

Focus on visual elements and their meaning.""",
            response_format="visual_analysis",
            include_visuals=True,
            include_sources=True,
            analysis_depth="comprehensive"
        )
        
        # Analytical template
        templates["analytical_response"] = ResponseTemplate(
            name="analytical_response",
            intent_type=QueryIntent.ANALYTICAL,
            system_prompt="""You are a research analyst expert. Provide deep analytical insights, 
            identify patterns, trends, and relationships in the data. Support conclusions with 
            evidence and explain methodologies when relevant.""",
            user_prompt_template="""Provide an analytical response to: {query}

Content for analysis:
{content}

Please provide a {analysis_depth} analysis that includes:
1. Key findings and insights
2. Data patterns and trends
3. Implications and significance
4. Supporting evidence with citations
5. Methodological considerations if relevant

Focus on analytical depth and evidence-based conclusions.""",
            response_format="analytical_report",
            include_visuals=True,
            include_sources=True,
            analysis_depth="comprehensive"
        )
        
        # Comparative template
        templates["comparative_response"] = ResponseTemplate(
            name="comparative_response",
            intent_type=QueryIntent.COMPARATIVE,
            system_prompt="""You are an expert in comparative analysis. Compare and contrast 
            different data points, findings, or visual elements. Highlight similarities, 
            differences, and relationships between compared elements.""",
            user_prompt_template="""Compare and analyze: {query}

Content for comparison:
{content}

Please provide a {analysis_depth} comparative analysis that includes:
1. Clear comparison framework
2. Similarities and differences
3. Relative strengths and weaknesses
4. Contextual factors
5. Conclusions with supporting evidence

Structure your response with clear comparisons and evidence.""",
            response_format="comparative_analysis",
            include_visuals=True,
            include_sources=True,
            analysis_depth="detailed"
        )
        
        # Summary template
        templates["summary_response"] = ResponseTemplate(
            name="summary_response",
            intent_type=QueryIntent.SUMMARY,
            system_prompt="""You are an expert at creating clear, concise summaries. 
            Extract key points, main findings, and essential information while maintaining 
            accuracy and completeness.""",
            user_prompt_template="""Create a summary for: {query}

Content to summarize:
{content}

Please provide a {analysis_depth} summary that includes:
1. Main points and key findings
2. Important data and statistics
3. Significant conclusions
4. Relevant visual insights if applicable

Keep the summary clear, accurate, and well-organized.""",
            response_format="structured_summary",
            include_visuals=False,
            include_sources=True,
            analysis_depth="detailed"
        )
        
        return templates
    
    def _load_visual_keywords(self) -> List[str]:
        """Load keywords that indicate visual content requests."""
        return [
            'chart', 'graph', 'table', 'figure', 'diagram', 'image', 'plot',
            'visualization', 'visual', 'show', 'display', 'picture', 'drawing',
            'trend', 'pattern', 'data', 'statistics', 'numbers', 'values',
            'comparison', 'distribution', 'correlation', 'relationship'
        ]
    
    def _load_analytical_keywords(self) -> List[str]:
        """Load keywords that indicate analytical requests."""
        return [
            'analyze', 'analysis', 'insight', 'trend', 'pattern', 'correlation',
            'relationship', 'implication', 'significance', 'conclusion',
            'interpretation', 'meaning', 'impact', 'effect', 'cause',
            'reason', 'explanation', 'methodology', 'approach'
        ]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'what', 'when', 'where', 'why', 'how'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _extract_visual_keywords(self, query: str) -> List[str]:
        """Extract visual-related keywords."""
        keywords = self._extract_keywords(query)
        return [word for word in keywords if word in self.visual_keywords]
    
    def _detect_intent(self, query: str, keywords: List[str], visual_keywords: List[str]) -> QueryIntent:
        """Detect the primary intent of the query."""
        query_lower = query.lower()
        
        # Check for visual intent
        if visual_keywords or any(word in query_lower for word in ['chart', 'graph', 'table', 'figure', 'visual']):
            return QueryIntent.VISUAL
        
        # Check for comparative intent
        if self._is_comparative_query(query):
            return QueryIntent.COMPARATIVE
        
        # Check for analytical intent
        if any(word in keywords for word in self.analytical_keywords):
            return QueryIntent.ANALYTICAL
        
        # Check for summary intent
        if any(word in query_lower for word in ['summary', 'summarize', 'overview', 'main points']):
            return QueryIntent.SUMMARY
        
        # Check for factual intent
        if any(word in query_lower for word in ['what', 'when', 'where', 'who', 'which']):
            return QueryIntent.FACTUAL
        
        # Default to textual
        return QueryIntent.TEXTUAL
    
    def _calculate_confidence(self, query: str, intent: QueryIntent, keywords: List[str]) -> float:
        """Calculate confidence in the intent detection."""
        # Simple confidence calculation based on keyword matches
        base_confidence = 0.6
        
        # Adjust based on specific indicators
        if intent == QueryIntent.VISUAL and any(word in query.lower() for word in ['chart', 'graph', 'table']):
            base_confidence += 0.3
        
        if intent == QueryIntent.ANALYTICAL and any(word in keywords for word in ['analyze', 'analysis', 'insight']):
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    def _assess_complexity(self, query: str, keywords: List[str]) -> float:
        """Assess the complexity of the query."""
        complexity_score = 0.0
        
        # Length factor
        word_count = len(query.split())
        complexity_score += min(word_count / 20, 0.3)
        
        # Keyword complexity
        complex_keywords = ['analysis', 'correlation', 'relationship', 'implication', 'methodology']
        keyword_matches = sum(1 for word in keywords if word in complex_keywords)
        complexity_score += min(keyword_matches / 5, 0.3)
        
        # Question complexity
        if '?' in query:
            complexity_score += 0.2
        
        # Multiple aspects
        if any(word in query.lower() for word in ['and', 'also', 'additionally', 'furthermore']):
            complexity_score += 0.2
        
        return min(complexity_score, 1.0)
    
    def _requires_visuals(self, intent: QueryIntent, visual_keywords: List[str]) -> bool:
        """Determine if the query requires visual content."""
        return intent in [QueryIntent.VISUAL, QueryIntent.COMPARATIVE] or len(visual_keywords) > 0
    
    def _requires_analysis(self, intent: QueryIntent, keywords: List[str]) -> bool:
        """Determine if the query requires analytical processing."""
        return intent in [QueryIntent.ANALYTICAL, QueryIntent.COMPARATIVE] or any(word in keywords for word in self.analytical_keywords)
    
    def _select_template(self, intent: QueryIntent, complexity_score: float, requires_visuals: bool) -> str:
        """Select appropriate template based on analysis."""
        if intent == QueryIntent.VISUAL or requires_visuals:
            return "visual_response"
        elif intent == QueryIntent.ANALYTICAL:
            return "analytical_response"
        elif intent == QueryIntent.COMPARATIVE:
            return "comparative_response"
        elif intent == QueryIntent.SUMMARY:
            return "summary_response"
        else:
            return "basic_response"
    
    def _has_question_words(self, query: str) -> bool:
        """Check if query contains question words."""
        question_words = ['what', 'when', 'where', 'why', 'how', 'who', 'which', 'whose', 'whom']
        return any(word in query.lower() for word in question_words)
    
    def _is_comparative_query(self, query: str) -> bool:
        """Check if query is asking for comparison."""
        comparative_words = ['compare', 'comparison', 'versus', 'vs', 'difference', 'similar', 'different', 'contrast']
        return any(word in query.lower() for word in comparative_words)