"""
Advanced PDF processing module for academic whitepapers.
Handles complex PDF extraction with structure preservation.
"""

import re
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AcademicPDFProcessor:
    """Intelligent PDF processor for academic papers."""
    
    def __init__(self):
        self.section_patterns = [
            r'^\s*(\d+\.?\s+[A-Z][A-Za-z\s]+)\s*$',  # "1. Introduction"
            r'^\s*([A-Z][A-Z\s]{2,})\s*$',  # "INTRODUCTION"
            r'^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$',  # "Introduction"
            r'^\s*(Abstract|Introduction|Background|Methodology|Results|Discussion|Conclusion|References)\s*$',
        ]
        
        self.subsection_patterns = [
            r'^\s*(\d+\.\d+\.?\s+[A-Z][A-Za-z\s]+)\s*$',  # "2.1. Background"
            r'^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$',  # "Related Work"
        ]
    
    def extract_text_pdfplumber(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text using pdfplumber for better formatting preservation."""
        full_text = ""
        metadata = {"pages": 0, "extraction_method": "pdfplumber"}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata["pages"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Clean up common PDF artifacts
                            page_text = self._clean_pdf_text(page_text)
                            full_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"PDFplumber extraction failed: {e}")
            return self.extract_text_pypdf2(pdf_path)
            
        return full_text, metadata
    
    def extract_text_pypdf2(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """Fallback extraction using PyPDF2."""
        full_text = ""
        metadata = {"pages": 0, "extraction_method": "pypdf2"}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            page_text = self._clean_pdf_text(page_text)
                            full_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise
            
        return full_text, metadata
    
    def _clean_pdf_text(self, text: str) -> str:
        """Clean common PDF extraction artifacts."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Fix common hyphenation issues
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # Remove page numbers and headers/footers (simple heuristic)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip likely page numbers or short headers/footers
            if len(line) < 3 or line.isdigit() or re.match(r'^\d+\s*$', line):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Detect sections and subsections in academic text."""
        lines = text.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                if current_content:
                    current_content.append('')
                continue
            
            # Check for main sections
            section_match = self._match_section_pattern(line, self.section_patterns)
            if section_match:
                # Save previous section
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'start_line': current_section_start,
                        'end_line': line_num - 1,
                        'type': 'section'
                    })
                
                current_section = section_match
                current_section_start = line_num
                current_content = []
                continue
            
            # Check for subsections
            subsection_match = self._match_section_pattern(line, self.subsection_patterns)
            if subsection_match and current_section:
                # This is a subsection, add it to content with special formatting
                current_content.append(f"\n## {subsection_match}\n")
                continue
            
            # Regular content
            if current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip(),
                'start_line': current_section_start,
                'end_line': len(lines) - 1,
                'type': 'section'
            })
        
        return sections
    
    def _match_section_pattern(self, line: str, patterns: List[str]) -> Optional[str]:
        """Check if line matches any section pattern."""
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def create_intelligent_chunks(self, sections: List[Dict[str, Any]], 
                                filename: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Create intelligent chunks from detected sections."""
        chunks = []
        
        for section in sections:
            title = section['title']
            content = section['content']
            
            # For short sections, create one chunk
            if len(content) <= max_chunk_size:
                chunks.append({
                    'id': f"whitepaper_{filename}_{len(chunks)}",
                    'content': f"# {title}\n\n{content}",
                    'source': 'whitepaper',
                    'section': title,
                    'filename': filename,
                    'chunk_type': 'complete_section',
                    'word_count': len(content.split())
                })
            else:
                # For long sections, split intelligently
                sub_chunks = self._split_long_section(content, title, max_chunk_size)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'id': f"whitepaper_{filename}_{len(chunks)}",
                        'content': f"# {title} (Part {i+1})\n\n{sub_chunk}",
                        'source': 'whitepaper',
                        'section': f"{title} (Part {i+1})",
                        'filename': filename,
                        'chunk_type': 'section_part',
                        'word_count': len(sub_chunk.split())
                    })
        
        return chunks
    
    def _split_long_section(self, content: str, title: str, max_size: int) -> List[str]:
        """Split long sections at natural boundaries."""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            para_size = len(paragraph)
            
            if current_size + para_size > max_size and current_chunk:
                # Save current chunk and start new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = para_size
            else:
                current_chunk.append(paragraph)
                current_size += para_size
        
        # Add remaining content
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Complete PDF processing pipeline."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text
        text, metadata = self.extract_text_pdfplumber(pdf_path)
        
        if not text.strip():
            raise ValueError(f"No text extracted from {pdf_path}")
        
        logger.info(f"Extracted {len(text)} characters from {metadata['pages']} pages")
        
        # Detect sections
        sections = self.detect_sections(text)
        logger.info(f"Detected {len(sections)} sections")
        
        # Create chunks
        filename = Path(pdf_path).stem
        chunks = self.create_intelligent_chunks(sections, filename)
        
        # Add metadata to all chunks
        for chunk in chunks:
            chunk.update({
                'pdf_pages': metadata['pages'],
                'extraction_method': metadata['extraction_method'],
                'pdf_path': pdf_path
            })
        
        logger.info(f"Created {len(chunks)} intelligent chunks")
        return chunks


def process_whitepaper_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Convenience function to process a single PDF."""
    processor = AcademicPDFProcessor()
    return processor.process_pdf(pdf_path)


if __name__ == "__main__":
    # Test with the DAG KNIGHT protocol
    test_pdf = "data/whitepapers/The DAG KNIGHT Protocol_Feb23_2023.pdf"
    if Path(test_pdf).exists():
        chunks = process_whitepaper_pdf(test_pdf)
        print(f"Processed {len(chunks)} chunks from {test_pdf}")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i+1}:")
            print(f"Section: {chunk['section']}")
            print(f"Content preview: {chunk['content'][:200]}...")
