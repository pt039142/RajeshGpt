"""RAG (Retrieval Augmented Generation) Service for grounded responses"""

from typing import List, Tuple, Optional
from pathlib import Path
import re
from app.core.config import settings


class RAGService:
    """
    Retrieval Augmented Generation service for grounded, accurate responses
    Uses document embeddings to retrieve relevant context before generating responses
    """
    
    def __init__(self):
        self.documents = {}  # In-memory document store
        self.embeddings = {}  # Document embeddings
        self.chunk_to_doc = {}  # Map chunks to document
        self.embeddings_dir = Path(settings.embeddings_dir)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase searchable terms."""
        return re.findall(r"[a-zA-Z0-9]+", text.lower())

    def _normalize_allowed_ids(self, allowed_document_ids: Optional[List]) -> Optional[set]:
        """Normalize allowed document identifiers to strings."""
        if not allowed_document_ids:
            return None
        return {str(doc_id) for doc_id in allowed_document_ids}

    def _score_chunks_from_documents(
        self,
        query: str,
        documents: List[dict],
        top_k: int = 5,
        similarity_threshold: float = 0.02,
    ) -> List[dict]:
        """Rank chunks from client-provided documents without storing them server-side."""
        relevant_chunks = []
        query_words = set(self._tokenize(query))

        for document in documents:
            doc_id = str(document.get("doc_id") or "")
            doc_name = document.get("name") or "Uploaded document"
            chunks = document.get("chunks") or []

            for chunk_idx, chunk_text in enumerate(chunks):
                chunk_text = str(chunk_text or "")
                chunk_words = set(self._tokenize(chunk_text))

                intersection = query_words & chunk_words
                union = query_words | chunk_words
                similarity = len(intersection) / len(union) if union else 0
                phrase_bonus = 0.0
                for token in query_words:
                    if token and token in chunk_text.lower():
                        phrase_bonus += 0.02
                final_score = similarity + min(0.2, phrase_bonus)

                if final_score >= similarity_threshold:
                    relevant_chunks.append({
                        "chunk_id": f"{doc_id}_{chunk_idx}",
                        "doc_id": doc_id,
                        "public_id": doc_id,
                        "doc_name": doc_name,
                        "chunk_index": chunk_idx,
                        "text": chunk_text,
                        "similarity": round(final_score, 4),
                        "metadata": {
                            "pages": document.get("pages", 0),
                            "storage": "client",
                        },
                    })

        relevant_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return relevant_chunks[:top_k]
    
    def add_document(
        self,
        doc_id: str,
        public_id: int,
        doc_name: str,
        chunks: List[str],
        metadata: dict
    ) -> bool:
        """
        Add document and its chunks to RAG system
        
        Args:
            doc_id: Unique document identifier
            doc_name: Document filename
            chunks: List of text chunks
            metadata: Document metadata
        """
        try:
            self.documents[doc_id] = {
                "id": public_id,
                "name": doc_name,
                "chunks": chunks,
                "metadata": metadata,
                "chunk_count": len(chunks)
            }
            
            # Map chunks to document
            for idx, chunk in enumerate(chunks):
                chunk_key = f"{doc_id}_{idx}"
                self.chunk_to_doc[chunk_key] = {
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "chunk_index": idx
                }
            
            return True
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False
    
    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.02,
        allowed_document_ids: Optional[List] = None,
    ) -> List[dict]:
        """
        Retrieve relevant chunks based on query
        Uses simple keyword matching and relevance scoring
        
        Returns:
            List of relevant chunks with metadata
        """
        relevant_chunks = []
        
        query_words = set(self._tokenize(query))
        allowed_ids = self._normalize_allowed_ids(allowed_document_ids)
        
        for chunk_key, chunk_loc in self.chunk_to_doc.items():
            doc_id = chunk_loc["doc_id"]
            chunk_idx = chunk_loc["chunk_index"]
            document = self.documents[doc_id]

            if allowed_ids is not None:
                public_id = str(document["id"])
                if doc_id not in allowed_ids and public_id not in allowed_ids:
                    continue
            
            chunk_text = document["chunks"][chunk_idx]
            chunk_words = set(self._tokenize(chunk_text))
            
            intersection = query_words & chunk_words
            union = query_words | chunk_words
            similarity = len(intersection) / len(union) if union else 0
            phrase_bonus = 0.0
            for token in query_words:
                if token and token in chunk_text.lower():
                    phrase_bonus += 0.02
            final_score = similarity + min(0.2, phrase_bonus)
            
            if final_score >= similarity_threshold:
                relevant_chunks.append({
                    "chunk_id": chunk_key,
                    "doc_id": doc_id,
                    "public_id": document["id"],
                    "doc_name": chunk_loc["doc_name"],
                    "chunk_index": chunk_idx,
                    "text": chunk_text,
                    "similarity": round(final_score, 4),
                    "metadata": document["metadata"]
                })
        
        # Sort by similarity and return top_k
        relevant_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return relevant_chunks[:top_k]
    
    def build_rag_context(
        self,
        query: str,
        top_k: int = 5,
        allowed_document_ids: Optional[List] = None,
    ) -> Tuple[str, List[dict]]:
        """
        Build context for LLM using retrieved chunks
        
        Returns:
            (context_string, source_chunks)
        """
        relevant_chunks = self.retrieve_relevant_chunks(
            query,
            top_k=top_k,
            allowed_document_ids=allowed_document_ids,
        )
        
        if not relevant_chunks:
            return "", []
        
        context_parts = []
        sources = []
        
        for chunk in relevant_chunks:
            context_parts.append(
                f"[{chunk['doc_name']} - Chunk {chunk['chunk_index']}]\n{chunk['text']}"
            )
            sources.append({
                "doc_id": chunk["doc_id"],
                "public_id": chunk["public_id"],
                "doc_name": chunk["doc_name"],
                "chunk_index": chunk["chunk_index"],
                "similarity": chunk["similarity"],
                "text": chunk["text"],
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        return context, sources

    def build_rag_context_from_documents(
        self,
        query: str,
        documents: List[dict],
        top_k: int = 5,
    ) -> Tuple[str, List[dict]]:
        """Build RAG context from client-provided documents sent with the request."""
        relevant_chunks = self._score_chunks_from_documents(
            query,
            documents,
            top_k=top_k,
        )

        if not relevant_chunks:
            return "", []

        context_parts = []
        sources = []

        for chunk in relevant_chunks:
            context_parts.append(
                f"[{chunk['doc_name']} - Chunk {chunk['chunk_index']}]\n{chunk['text']}"
            )
            sources.append({
                "doc_id": chunk["doc_id"],
                "public_id": chunk["public_id"],
                "doc_name": chunk["doc_name"],
                "chunk_index": chunk["chunk_index"],
                "similarity": chunk["similarity"],
                "text": chunk["text"],
            })

        return "\n\n---\n\n".join(context_parts), sources
    
    def get_document_info(self, doc_id: str) -> Optional[dict]:
        """Get information about a document"""
        return self.documents.get(doc_id)
    
    def list_documents(self) -> List[dict]:
        """List all documents in RAG system"""
        docs = []
        for doc_id, doc_info in self.documents.items():
            docs.append({
                "id": doc_info["id"],
                "doc_id": doc_id,
                "name": doc_info["name"],
                "chunk_count": doc_info["chunk_count"],
                "metadata": doc_info["metadata"]
            })
        return docs
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove document from RAG system"""
        try:
            if doc_id in self.documents:
                file_path = self.documents[doc_id]["metadata"].get("file_path")
                # Remove chunks
                keys_to_remove = [k for k in self.chunk_to_doc.keys() if k.startswith(doc_id)]
                for key in keys_to_remove:
                    del self.chunk_to_doc[key]
                
                # Remove document
                del self.documents[doc_id]
                if file_path:
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except OSError:
                        pass
                return True
            return False
        except Exception as e:
            print(f"Error removing document: {str(e)}")
            return False


# Global RAG instance
rag_service = RAGService()
