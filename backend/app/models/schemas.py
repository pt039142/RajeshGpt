"""Pydantic schemas for API requests/responses"""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: str
    full_name: str


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class User(UserBase):
    """User response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response wrapper"""
    success: bool
    message: str
    data: Optional[User] = None


# Document Schemas
class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str
    document_type: str = "pdf"


class DocumentCreate(DocumentBase):
    """Document creation schema"""
    pass


class Document(DocumentBase):
    """Document response schema"""
    id: int
    doc_id: Optional[str] = None
    user_id: Optional[int] = None
    file_path: str
    file_size: int
    pages: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document response wrapper"""
    success: bool
    message: str
    data: Optional[Document] = None


# Query Schemas
class QueryRequest(BaseModel):
    """Income tax query request"""
    query: str = Field(..., min_length=5, max_length=1000)
    document_ids: Optional[List[Union[int, str]]] = []
    conversation_id: Optional[str] = None


class QueryValidation(BaseModel):
    """Query validation result"""
    is_valid: bool
    confidence: float
    reason: Optional[str] = None
    scope: str  # "in_scope", "out_of_scope", "mixed"


class Citation(BaseModel):
    """Citation reference"""
    document_name: str
    page_number: int
    section: str
    text: str


class QueryResponse(BaseModel):
    """Query response"""
    query: str
    response: str
    citations: List[Citation] = []
    model: Optional[str] = None
    confidence_score: float
    has_hallucination_risk: bool
    scope: str
    timestamp: datetime


class ConversationMessage(BaseModel):
    """Message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    citations: List[Citation] = []


class ConversationResponse(BaseModel):
    """Conversation response wrapper"""
    success: bool
    message: str
    data: Optional[QueryResponse] = None
    validation: Optional[QueryValidation] = None


# Health Check
class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: dict


# Error Response
class ErrorResponse(BaseModel):
    """Error response wrapper"""
    success: bool = False
    error: str
    details: Optional[dict] = None
