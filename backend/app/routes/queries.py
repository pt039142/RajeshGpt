"""Query and response endpoints"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, ConversationResponse
from app.services.validation_service import query_validator, hallucination_detector
from app.services.rag_service import rag_service
from app.services.llm_service import get_llm_service
from app.core.config import settings
from datetime import datetime
import uuid

router = APIRouter()

# Conversation history (in-memory for demo)
conversations = {}


@router.post("/query", response_model=ConversationResponse)
async def process_query(request: QueryRequest):
    """Process an income tax query"""
    
    try:
        # Initialize conversation if needed
        conv_id = request.conversation_id or str(uuid.uuid4())
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        # 1. Validate query
        validation = query_validator.validate_query(request.query)
        
        if not query_validator.should_respond(validation):
            return {
                "success": False,
                "message": query_validator.get_rejection_message(validation),
                "validation": validation
            }
        
        available_documents = rag_service.list_documents()
        requested_document_ids = request.document_ids or []
        allowed_document_ids = requested_document_ids or [doc["doc_id"] for doc in available_documents]

        if available_documents:
            rag_context, source_chunks = rag_service.build_rag_context(
                request.query,
                top_k=5,
                allowed_document_ids=allowed_document_ids,
            )
        else:
            rag_context = ""
            source_chunks = []
        
        # 4. Generate response using LLM
        llm = get_llm_service()
        llm_result = llm.generate_response(
            query=request.query,
            context=rag_context,
            system_prompt=settings.system_prompt
        )
        
        # 5. Check for hallucination risk
        hallucination_check = hallucination_detector.check_response(
            response=llm_result["response"],
            source_documents=source_chunks,
            confidence_score=llm_result.get("confidence", 0.5)
        )
        
        # 6. Extract citations
        citations = []
        for chunk in source_chunks:
            citations.append({
                "document_name": chunk["doc_name"],
                "page_number": chunk["chunk_index"],
                "section": f"Section {chunk['chunk_index']}",
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            })

        if requested_document_ids and not source_chunks:
            llm_result["response"] += (
                "\n\nNo highly relevant passage was found in the selected uploaded document set. "
                "Try selecting a different PDF or ask a narrower question tied to the uploaded material."
            )
        
        # 7. Construct response
        response_data = {
            "query": request.query,
            "response": llm_result["response"],
            "citations": citations,
            "model": llm_result.get("model"),
            "confidence_score": llm_result.get("confidence", 0.5),
            "has_hallucination_risk": hallucination_check["has_risk"],
            "scope": validation["scope"],
            "timestamp": datetime.utcnow()
        }
        
        # Add to conversation history
        conversations[conv_id].append({
            "role": "user",
            "content": request.query,
            "timestamp": datetime.utcnow()
        })
        
        conversations[conv_id].append({
            "role": "assistant",
            "content": llm_result["response"],
            "citations": citations,
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "message": "Response generated successfully",
            "data": response_data,
            "validation": validation
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get conversation history"""
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        history = conversations[conversation_id]
        
        return {
            "success": True,
            "message": "Conversation history retrieved",
            "conversation_id": conversation_id,
            "messages": history,
            "total_messages": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/query/history/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation"""
    try:
        if conversation_id in conversations:
            del conversations[conversation_id]
        
        return {
            "success": True,
            "message": "Conversation deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/validate")
async def validate_query(query: str):
    """Validate a query without generating response"""
    try:
        validation = query_validator.validate_query(query)
        
        return {
            "success": True,
            "message": "Query validation complete",
            "validation": validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
