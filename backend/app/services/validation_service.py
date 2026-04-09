"""Query Validation and Scope Detection Service"""

from typing import Tuple, Optional
from app.core.config import settings


class QueryValidator:
    """Validate queries and detect if they're in scope for Income Tax guidance"""
    
    def __init__(self):
        self.in_scope_keywords = settings.in_scope_keywords
        self.out_of_scope_keywords = settings.out_of_scope_keywords
    
    def validate_query(self, query: str) -> dict:
        """
        Validate if query is appropriate for RajeshGPT
        
        Returns:
            {
                "is_valid": bool,
                "confidence": float (0-1),
                "scope": "in_scope" | "out_of_scope" | "mixed",
                "reason": str,
                "warnings": list
            }
        """
        query_lower = query.lower()
        warnings = []
        
        # Check for out of scope keywords
        out_scope_matches = self._check_keywords(query_lower, self.out_of_scope_keywords)
        
        # Check for in scope keywords
        in_scope_matches = self._check_keywords(query_lower, self.in_scope_keywords)
        
        # Determine scope and confidence
        if len(out_scope_matches) > len(in_scope_matches):
            scope = "out_of_scope"
            confidence = 0.9
            reason = f"Query contains out-of-scope topics: {', '.join(out_scope_matches)}"
            is_valid = False
        
        elif len(in_scope_matches) > 0:
            scope = "in_scope"
            confidence = min(0.95, 0.7 + (len(in_scope_matches) * 0.1))
            reason = "Query is related to tax, finance, accounting, or compliance"
            is_valid = True
        
        else:
            scope = "mixed"
            confidence = 0.58
            reason = "Query is broad, but it can still be handled as a finance, business, or compliance question"
            is_valid = True
            warnings.append("For stronger answers, mention the tax, finance, or accounting context more specifically.")
        
        # Check query length
        if len(query) < 10:
            warnings.append("Query is very short. Consider providing more context.")
            confidence *= 0.9
        
        if len(query) > 1000:
            warnings.append("Query is very long. Please break it into smaller questions.")
            confidence *= 0.9
        
        return {
            "is_valid": is_valid,
            "confidence": min(1.0, max(0.0, confidence)),
            "scope": scope,
            "reason": reason,
            "warnings": warnings
        }
    
    def _check_keywords(self, text: str, keywords: list) -> list:
        """Check which keywords are present in text"""
        matches = []
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(keyword)
        return matches
    
    def should_respond(self, validation: dict) -> bool:
        """Determine if assistant should provide a substantive response"""
        return validation["is_valid"]
    
    def get_rejection_message(self, validation: dict) -> str:
        """Get appropriate rejection message"""
        if validation["scope"] == "out_of_scope":
            return (
                "I'm specialized in tax, finance, compliance, and CA-related guidance. Your question appears to be outside that domain. "
                "Please consult the appropriate professional for this inquiry."
            )
        else:
            return (
                "I can answer finance, tax, accounting, and compliance questions more effectively if you rephrase with a bit more business or tax context."
            )


class HallucinationDetector:
    """Detect potential hallucinations in responses"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def check_response(
        self, 
        response: str, 
        source_documents: list,
        confidence_score: float
    ) -> dict:
        """
        Check if response might contain hallucinations
        
        Returns:
            {
                "has_risk": bool,
                "confidence": float,
                "flags": list,
                "recommendation": str
            }
        """
        flags = []
        risk_score = 0.0
        
        # Check if no source documents provided
        if not source_documents or len(source_documents) == 0:
            flags.append("No source documents provided")
            risk_score += 0.4
        
        # Check confidence score
        if confidence_score < self.confidence_threshold:
            flags.append(f"Low confidence score: {confidence_score:.2f}")
            risk_score += 0.3
        
        # Check for uncertain language patterns
        uncertain_phrases = [
            "probably", "might", "could", "supposedly",
            "allegedly", "is said to", "reportedly"
        ]
        
        response_lower = response.lower()
        uncertain_count = sum(1 for phrase in uncertain_phrases if phrase in response_lower)
        if uncertain_count > 3:
            flags.append(f"Excessive uncertain language ({uncertain_count} instances)")
            risk_score += 0.2
        
        # Check for overly specific claims without citations
        if "%" in response and len(source_documents) == 0:
            flags.append("Specific percentages mentioned without source documents")
            risk_score += 0.2
        
        has_risk = risk_score > 0.3
        
        recommendation = "Response is factually grounded" if not has_risk else \
                        "Verify response with additional sources before acting on it"
        
        return {
            "has_risk": has_risk,
            "confidence": min(1.0, max(0.0, 1.0 - risk_score)),
            "flags": flags,
            "recommendation": recommendation
        }


# Global instances
query_validator = QueryValidator()
hallucination_detector = HallucinationDetector()
