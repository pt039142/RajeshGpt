"""PDF Processing and Document Management Service"""

import PyPDF2
from typing import List, Tuple
from pathlib import Path
from io import BytesIO
from app.core.config import settings


class PDFProcessor:
    """Handle PDF document processing and text extraction"""
    
    def __init__(self):
        self.max_size = settings.max_pdf_size_mb * 1024 * 1024
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_pdf(self, file_path: str, file_size: int) -> Tuple[bool, str]:
        """Validate PDF file"""
        # Check size
        if file_size > self.max_size:
            return False, f"File size exceeds {settings.max_pdf_size_mb}MB limit"
        
        # Check format
        if not file_path.lower().endswith('.pdf'):
            return False, "Only PDF files are supported"
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if len(reader.pages) == 0:
                    return False, "PDF has no pages"
        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"
        
        return True, "PDF validation successful"

    def validate_pdf_bytes(self, filename: str, file_content: bytes) -> Tuple[bool, str]:
        """Validate PDF content directly from bytes."""
        if len(file_content) > self.max_size:
            return False, f"File size exceeds {settings.max_pdf_size_mb}MB limit"

        if not filename.lower().endswith(".pdf"):
            return False, "Only PDF files are supported"

        try:
            reader = PyPDF2.PdfReader(BytesIO(file_content))
            if len(reader.pages) == 0:
                return False, "PDF has no pages"
        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"

        return True, "PDF validation successful"
    
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, int]:
        """Extract text from PDF file"""
        text = ""
        pages = 0
        
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pages = len(reader.pages)
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        
        return text, pages
    
    def extract_text_with_metadata(self, file_path: str) -> dict:
        """Extract text and metadata from PDF"""
        text = ""
        metadata = {}
        pages = 0
        page_contents = []
        
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # Extract metadata
                if reader.metadata:
                    metadata = {
                        "title": reader.metadata.get("/Title", ""),
                        "author": reader.metadata.get("/Author", ""),
                        "subject": reader.metadata.get("/Subject", ""),
                        "creator": reader.metadata.get("/Creator", ""),
                    }
                
                pages = len(reader.pages)
                
                # Extract text from each page
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    text += page_text + "\n"
                    page_contents.append({
                        "page_number": page_num,
                        "content": page_text
                    })
        
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
        return {
            "full_text": text,
            "metadata": metadata,
            "pages": pages,
            "page_contents": page_contents
        }

    def extract_text_with_metadata_from_bytes(self, file_content: bytes) -> dict:
        """Extract text and metadata from in-memory PDF bytes."""
        text = ""
        metadata = {}
        pages = 0
        page_contents = []

        try:
            reader = PyPDF2.PdfReader(BytesIO(file_content))

            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }

            pages = len(reader.pages)

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                text += page_text + "\n"
                page_contents.append({
                    "page_number": page_num,
                    "content": page_text
                })

        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

        return {
            "full_text": text,
            "metadata": metadata,
            "pages": pages,
            "page_contents": page_contents
        }
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into chunks for embedding"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                # Keep overlap
                overlap_words = overlap // 5  # Rough estimate
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_size = sum(len(w) for w in current_chunk)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk"""
        file_path = self.upload_dir / filename
        file_path.write_bytes(file_content)
        return str(file_path)


# Global PDF processor instance
pdf_processor = PDFProcessor()
