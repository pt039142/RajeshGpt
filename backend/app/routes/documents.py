"""Document upload and management endpoints"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import DocumentResponse, Document
from app.services.pdf_service import pdf_processor
from app.services.rag_service import rag_service
from app.core.config import settings
import os
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    
    try:
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        public_id = int(doc_id[:8], 16) % (2**31)
        
        # Read file
        file_content = await file.read()
        file_size = len(file_content)
        
        is_valid, validation_msg = pdf_processor.validate_pdf_bytes(
            file.filename,
            file_content,
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)
        
        # Save file properly
        save_path = os.path.join(settings.upload_dir, f"{doc_id}_{file.filename}")
        pdf_processor.save_uploaded_file(file_content, f"{doc_id}_{file.filename}")
        
        # Extract text and metadata
        doc_data = pdf_processor.extract_text_with_metadata_from_bytes(file_content)
        
        # Chunk text for RAG
        chunks = pdf_processor.chunk_text(doc_data["full_text"])
        
        # Add to RAG system
        rag_service.add_document(
            doc_id=doc_id,
            public_id=public_id,
            doc_name=file.filename,
            chunks=chunks,
            metadata={
                "file_path": save_path,
                "file_size": file_size,
                "pages": doc_data["pages"],
                "pdf_metadata": doc_data["metadata"]
            }
        )
        
        return {
            "success": True,
            "message": "Document uploaded and processed successfully",
            "data": {
                "id": public_id,
                "doc_id": doc_id,
                "filename": file.filename,
                "document_type": "pdf",
                "file_path": save_path,
                "file_size": file_size,
                "pages": doc_data["pages"],
                "chunk_count": len(chunks),
                "chunks": chunks,
                "uploaded_at": datetime.utcnow()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = rag_service.list_documents()
        return {
            "success": True,
            "message": "Documents retrieved successfully",
            "data": documents,
            "total": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document details"""
    try:
        doc = rag_service.get_document_info(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": "Document retrieved successfully",
            "data": {
                "doc_id": doc_id,
                "name": doc["name"],
                "chunk_count": doc["chunk_count"],
                "metadata": doc["metadata"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    try:
        success = rag_service.remove_document(doc_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
