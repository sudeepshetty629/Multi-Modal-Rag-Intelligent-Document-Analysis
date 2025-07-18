"""
Phase 1: Intelligent Document Decomposition
This phase breaks down complex documents into structured, interconnected data elements.
"""

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import io
import base64
import json
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path
import os

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of document content with metadata."""
    id: str
    content: str
    page_number: int
    chunk_index: int
    content_type: str  # 'text', 'table', 'image', 'chart'
    metadata: Dict[str, Any]
    section_hierarchy: List[str]
    visual_link: Optional[str] = None  # Link to associated visual content

@dataclass
class VisualElement:
    """Represents a visual element extracted from the document."""
    id: str
    type: str  # 'chart', 'table', 'diagram', 'image'
    page_number: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    image_data: str  # Base64 encoded image
    caption: Optional[str] = None
    description: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None  # For tables

class DocumentDecomposer:
    """Handles the decomposition of PDF documents into structured elements."""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        
    def decompose_document(self, file_path: str, document_id: str) -> Tuple[List[DocumentChunk], List[VisualElement]]:
        """
        Decompose a document into chunks and visual elements.
        
        Args:
            file_path: Path to the document file
            document_id: Unique identifier for the document
            
        Returns:
            Tuple of (text_chunks, visual_elements)
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document not found: {file_path}")
                
            # Extract text and structure
            text_chunks = self._extract_text_chunks(file_path, document_id)
            
            # Extract visual elements
            visual_elements = self._extract_visual_elements(file_path, document_id)
            
            # Link visuals to text chunks
            self._link_visuals_to_text(text_chunks, visual_elements)
            
            logger.info(f"Decomposed document {document_id}: {len(text_chunks)} text chunks, {len(visual_elements)} visual elements")
            
            return text_chunks, visual_elements
            
        except Exception as e:
            logger.error(f"Error decomposing document {document_id}: {str(e)}")
            raise
    
    def _extract_text_chunks(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        """Extract text chunks with layout-aware parsing."""
        chunks = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text with layout information
                text_elements = page.extract_text_lines()
                
                # Group into logical chunks
                current_chunk = []
                current_section = []
                chunk_index = 0
                
                for line in text_elements:
                    text = line.get('text', '').strip()
                    if not text:
                        continue
                        
                    # Detect section headers (simple heuristic)
                    if self._is_section_header(text):
                        if current_chunk:
                            # Save previous chunk
                            chunk = self._create_text_chunk(
                                document_id, page_num, chunk_index, 
                                current_chunk, current_section
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                            current_chunk = []
                        
                        current_section = [text]
                    else:
                        current_chunk.append(text)
                
                # Save final chunk for the page
                if current_chunk:
                    chunk = self._create_text_chunk(
                        document_id, page_num, chunk_index, 
                        current_chunk, current_section
                    )
                    chunks.append(chunk)
                    
        return chunks
    
    def _extract_visual_elements(self, file_path: str, document_id: str) -> List[VisualElement]:
        """Extract visual elements (images, charts, tables) from the document."""
        visual_elements = []
        
        # Use PyMuPDF for image extraction
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n < 5:  # GRAY or RGB
                        img_data = pix.pil_tobytes(format="PNG")
                        img_base64 = base64.b64encode(img_data).decode()
                        
                        # Get image bbox
                        img_rects = page.get_image_rects(img)
                        if img_rects:
                            bbox = img_rects[0]
                            
                            visual_element = VisualElement(
                                id=f"{document_id}_visual_{page_num}_{img_index}",
                                type=self._classify_visual_type(img_data),
                                page_number=page_num,
                                bbox=(bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                                image_data=img_base64,
                                description=f"Visual element on page {page_num + 1}"
                            )
                            visual_elements.append(visual_element)
                    
                    pix = None
                    
                except Exception as e:
                    logger.warning(f"Error extracting image {img_index} from page {page_num}: {str(e)}")
                    continue
        
        doc.close()
        
        # Extract tables using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table_index, table in enumerate(tables):
                    if table:
                        # Convert table to structured data
                        structured_data = self._process_table_data(table)
                        
                        # Create table visualization
                        table_image = self._create_table_image(table)
                        
                        visual_element = VisualElement(
                            id=f"{document_id}_table_{page_num}_{table_index}",
                            type="table",
                            page_number=page_num,
                            bbox=(0, 0, 0, 0),  # pdfplumber doesn't provide bbox easily
                            image_data=table_image,
                            description=f"Table on page {page_num + 1}",
                            structured_data=structured_data
                        )
                        visual_elements.append(visual_element)
        
        return visual_elements
    
    def _is_section_header(self, text: str) -> bool:
        """Simple heuristic to detect section headers."""
        # Check for common patterns
        patterns = [
            text.isupper() and len(text) < 100,
            text.endswith(':') and len(text) < 100,
            any(text.startswith(prefix) for prefix in ['Chapter', 'Section', 'Abstract', 'Introduction', 'Conclusion', 'References'])
        ]
        return any(patterns)
    
    def _create_text_chunk(self, document_id: str, page_num: int, chunk_index: int, 
                          text_lines: List[str], section_hierarchy: List[str]) -> DocumentChunk:
        """Create a text chunk with metadata."""
        content = '\n'.join(text_lines)
        
        return DocumentChunk(
            id=f"{document_id}_chunk_{page_num}_{chunk_index}",
            content=content,
            page_number=page_num,
            chunk_index=chunk_index,
            content_type='text',
            metadata={
                'word_count': len(content.split()),
                'char_count': len(content),
                'language': 'en',  # Could be detected
                'extraction_method': 'pdfplumber'
            },
            section_hierarchy=section_hierarchy
        )
    
    def _classify_visual_type(self, img_data: bytes) -> str:
        """Classify the type of visual element."""
        # Simple classification based on image properties
        # This could be enhanced with ML models
        try:
            img = Image.open(io.BytesIO(img_data))
            width, height = img.size
            
            # Simple heuristics
            if width > height * 1.5:  # Wide images might be charts
                return 'chart'
            elif width < height * 0.8:  # Tall images might be diagrams
                return 'diagram'
            else:
                return 'image'
                
        except Exception:
            return 'image'
    
    def _process_table_data(self, table: List[List[str]]) -> Dict[str, Any]:
        """Process table data into structured format."""
        if not table:
            return {}
            
        # Assume first row is headers
        headers = table[0] if table else []
        rows = table[1:] if len(table) > 1 else []
        
        return {
            'headers': headers,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(headers),
            'data_types': self._infer_column_types(rows, headers)
        }
    
    def _infer_column_types(self, rows: List[List[str]], headers: List[str]) -> Dict[str, str]:
        """Infer data types for table columns."""
        types = {}
        
        for col_idx, header in enumerate(headers):
            if col_idx < len(rows[0]) if rows else False:
                sample_values = [row[col_idx] for row in rows if col_idx < len(row)]
                
                # Simple type inference
                if all(self._is_numeric(val) for val in sample_values if val):
                    types[header] = 'numeric'
                elif all(self._is_date(val) for val in sample_values if val):
                    types[header] = 'date'
                else:
                    types[header] = 'text'
                    
        return types
    
    def _is_numeric(self, value: str) -> bool:
        """Check if a value is numeric."""
        try:
            float(value.replace(',', '').replace('$', '').replace('%', ''))
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_date(self, value: str) -> bool:
        """Check if a value looks like a date."""
        import re
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\w+ \d{1,2}, \d{4}'
        ]
        return any(re.match(pattern, str(value)) for pattern in date_patterns)
    
    def _create_table_image(self, table: List[List[str]]) -> str:
        """Create a simple visualization of the table."""
        # For now, return a placeholder
        # In a real implementation, you'd create an actual image
        return ""
    
    def _link_visuals_to_text(self, text_chunks: List[DocumentChunk], visual_elements: List[VisualElement]):
        """Link visual elements to nearby text chunks."""
        for visual in visual_elements:
            # Find chunks from the same page
            page_chunks = [chunk for chunk in text_chunks if chunk.page_number == visual.page_number]
            
            if page_chunks:
                # For now, link to the first chunk on the same page
                # In a real implementation, you'd use spatial proximity
                page_chunks[0].visual_link = visual.id