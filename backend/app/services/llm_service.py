"""LLM Integration Service"""

from typing import Any, List, Optional, Tuple
import os
import re
import requests


class LLMService:
    """
    Service for LLM integration with hallucination prevention
    """
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gpt-4",
        provider: str = "auto",
        huggingface_api_key: str = None,
        huggingface_model: str = "openai/gpt-oss-20b:cheapest",
        huggingface_base_url: str = "https://router.huggingface.co/v1/chat/completions",
        ollama_base_url: str = "http://127.0.0.1:11434",
        ollama_model: str = "qwen2.5:1.5b-instruct",
        ollama_fallback_models: Optional[List[str]] = None,
    ):
        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
        resolved_hf_api_key = huggingface_api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.client = None
        self.provider = provider
        self.huggingface_api_key = resolved_hf_api_key
        self.huggingface_model = huggingface_model or os.getenv(
            "HUGGINGFACE_MODEL",
            "openai/gpt-oss-20b:cheapest",
        )
        self.huggingface_base_url = (
            huggingface_base_url
            or os.getenv(
                "HUGGINGFACE_BASE_URL",
                "https://router.huggingface.co/v1/chat/completions",
            )
        )
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.ollama_model = ollama_model
        self.ollama_fallback_models = self._build_ollama_candidates(
            ollama_model,
            ollama_fallback_models or [],
        )
        self.last_ollama_error = None
        try:
            from openai import OpenAI
            if resolved_api_key and provider in ["auto", "openai"]:
                self.client = OpenAI(api_key=resolved_api_key)
        except ImportError:
            print("OpenAI library not installed. Using mock responses.")
        
        self.model_name = model_name
        self.temperature = 0.3  # Low temperature for consistency
        self.tax_knowledge = {
            "hello": "Hello. I can help with Indian tax, accounting, finance, compliance, company review, broker workflows, and document-backed analysis.",
            "hi": "Hello. I can help with Indian tax, accounting, finance, compliance, company review, broker workflows, and document-backed analysis.",
            "80c": "Section 80C generally covers eligible deductions up to Rs. 1,50,000 for items such as PF, PPF, ELSS, life insurance premium, certain tuition fees, and specified principal repayments.",
            "80d": "Section 80D generally covers deduction for medical insurance premium for self, family, and parents, with higher limits for senior citizens subject to the applicable conditions.",
            "80e": "Section 80E generally allows deduction for eligible education loan interest for up to eight assessment years, subject to the prescribed conditions.",
            "form 16": "Form 16 is the salary TDS certificate issued by the employer and is commonly used while preparing and reviewing the income tax return.",
            "tds": "TDS means tax deducted at source. The applicable rate depends on the type of payment such as salary, interest, rent, commission, or professional fees.",
            "gst": "GST is a destination-based indirect tax on supply of goods and services. Registration thresholds, rates, and filing frequency depend on business profile and turnover.",
            "capital gains": "Capital gains tax treatment depends on the nature of the asset, holding period, exemptions claimed, and whether the gain is short-term or long-term.",
            "salary": "Salary income analysis typically includes taxable salary components, exemptions, deductions, TDS reconciliation, and return disclosure requirements.",
            "audit": "Audit and review work usually focuses on supporting documentation, statutory compliance, accounting treatment, and whether the tax position is properly evidenced.",
            "company": "Company tax review generally covers income classification, admissible expenditure, depreciation, compliance dates, audit implications, and return filing requirements.",
            "stock exchange": "A stock exchange is a regulated marketplace where shares, bonds, and other securities are listed and traded under defined rules, disclosure requirements, and surveillance controls.",
            "broker": "A broker or securities intermediary facilitates investor trades, account opening, fund settlement, research access, and regulatory compliance through an exchange and depository ecosystem.",
            "securities": "Securities businesses typically operate through trading accounts, demat accounts, exchange connectivity, settlement processes, margin controls, and compliance supervision.",
            "finance": "Financial analysis usually focuses on revenue, profit, cost structure, working capital, cash flow, funding, compliance exposure, and the quality of documentation supporting those numbers.",
            "accounting": "Accounting support generally includes journal treatment, ledger review, balance sheet impact, profit and loss presentation, depreciation, provisions, reconciliations, and disclosure quality.",
            "balance sheet": "Balance sheet review usually focuses on assets, liabilities, reserves, receivables, payables, borrowings, and whether balances are properly supported and classified.",
            "cash flow": "Cash flow analysis usually reviews operating, investing, and financing movement, liquidity position, mismatch risk, and whether cash generation supports the business model.",
            "profit": "Profit analysis usually considers gross margin, operating margin, finance cost, tax impact, exceptional items, and whether profitability is sustainable or one-off.",
            "loss": "Loss analysis usually reviews the reasons for decline, fixed versus variable cost pressure, finance burden, provisioning, impairment, and whether tax treatment or set-off is available.",
            "working capital": "Working capital analysis usually reviews inventory cycle, receivable days, payable days, cash conversion, and pressure on short-term funding.",
            "ratio": "Financial ratio analysis generally includes liquidity ratios, leverage ratios, profitability ratios, and efficiency ratios, interpreted together rather than in isolation.",
            "compliance": "Compliance support usually covers due dates, filing obligations, supporting records, notices, reconciliations, and whether internal controls reduce reporting risk.",
            "notice": "A notice response workflow generally includes identifying the section involved, verifying facts from records, matching the return data, collecting support papers, and preparing a focused written reply.",
        }

    def _build_ollama_candidates(
        self,
        primary_model: str,
        fallback_models: List[str],
    ) -> List[str]:
        """Return an ordered de-duplicated list of candidate Ollama models."""
        candidates = [primary_model, *fallback_models]
        normalized = []
        seen = set()
        for model in candidates:
            cleaned = str(model or "").strip()
            if not cleaned or cleaned in seen:
                continue
            normalized.append(cleaned)
            seen.add(cleaned)
        return normalized

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for lightweight matching."""
        return re.findall(r"[a-zA-Z0-9]+", text.lower())

    def _extract_context_lines(self, context: str, limit: int = 4) -> List[str]:
        """Extract concise lines from retrieved context."""
        cleaned = []
        for line in context.splitlines():
            line = line.strip()
            if not line or line.startswith("[") or line == "---":
                continue
            cleaned.append(line)
        return cleaned[:limit]

    def _knowledge_response(self, query: str) -> str:
        """Return the best deterministic knowledge-base match."""
        query_lower = query.lower()
        for keyword, answer in self.tax_knowledge.items():
            if keyword in query_lower:
                return answer
        return (
            "RajeshGPT is focused on Indian income tax, finance, accounting, compliance, and CA workflows. "
            "Please ask a more specific question about deductions, filing, notices, TDS, GST, company tax, audit support, accounting treatment, or financial review."
        )

    def _build_messages(self, query: str, context: str = "", system_prompt: str = None) -> List[dict]:
        """Build provider-neutral chat messages."""
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        if context:
            user_message = f"""Use the following retrieved tax or document context while answering.

Question: {query}

Context:
{context}

Instructions:
1. Prefer the provided context when it is relevant.
2. If the context is insufficient, say what is missing.
3. Keep the answer concise, professional, and suitable for tax review work.
4. Mention when the answer is document-backed."""
        else:
            user_message = f"""Question: {query}

Provide a professional answer focused on Indian income tax, finance, accounting, compliance, company operations, or CA workflows.
If the user asks about a company, stock exchange, broker, finance concept, or greeting, answer directly and practically instead of rejecting the question.
If the topic is outside finance, tax, accounting, or compliance, say so briefly."""

        messages.append({
            "role": "user",
            "content": user_message,
        })
        return messages

    def _extract_message_text(self, content: Any) -> str:
        """Normalize provider response content into plain text."""
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
            return "\n".join(parts).strip()

        return str(content or "").strip()

    def _ollama_chat(
        self,
        model: str,
        query: str,
        context: str = "",
        system_prompt: str = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Call a specific Ollama model and return either content or an error."""
        try:
            payload = {
                "model": model,
                "messages": self._build_messages(query, context, system_prompt),
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                },
            }
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            content = (
                data.get("message", {}).get("content")
                or data.get("response")
                or ""
            ).strip()
            if not content:
                return None, "Ollama returned an empty response"
            return {
                "response": content,
                "confidence": 0.88 if context else 0.72,
                "sources_used": bool(context),
                "model": f"{model} (Ollama)",
            }, None
        except Exception as exc:
            return None, str(exc)

    def _generate_ollama_response(self, query: str, context: str = "", system_prompt: str = None) -> Optional[dict]:
        """Generate a response from a local Ollama server if available."""
        self.last_ollama_error = None
        for candidate in self.ollama_fallback_models:
            result, error = self._ollama_chat(candidate, query, context, system_prompt)
            if result is not None:
                return result
            self.last_ollama_error = error
            if error and "requires more system memory" in error.lower():
                continue
        return None

    def _huggingface_chat(
        self,
        query: str,
        context: str = "",
        system_prompt: str = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Call Hugging Face Inference Providers via the OpenAI-compatible chat endpoint."""
        if not self.huggingface_api_key:
            return None, "Hugging Face API key is not configured"

        try:
            response = requests.post(
                self.huggingface_base_url,
                headers={
                    "Authorization": f"Bearer {self.huggingface_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.huggingface_model,
                    "messages": self._build_messages(query, context, system_prompt),
                    "temperature": self.temperature,
                    "max_tokens": 2048,
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            message = choices[0].get("message", {}) if choices else {}
            content = self._extract_message_text(message.get("content"))
            if not content:
                return None, "Hugging Face returned an empty response"

            return {
                "response": content,
                "confidence": 0.84 if context else 0.66,
                "sources_used": bool(context),
                "model": data.get("model") or f"{self.huggingface_model} (Hugging Face)",
                "finish_reason": choices[0].get("finish_reason") if choices else None,
            }, None
        except requests.HTTPError as exc:
            details = ""
            try:
                details = exc.response.text.strip()
            except Exception:
                details = ""
            message = f"Hugging Face request failed with status {exc.response.status_code}"
            if details:
                message = f"{message}: {details}"
            return None, message
        except Exception as exc:
            return None, str(exc)

    def _build_grounded_response(self, query: str, context: str = "") -> dict:
        """Generate a strong local response without depending on external LLMs."""
        base_answer = self._knowledge_response(query)
        context_lines = self._extract_context_lines(context)

        if context_lines:
            response_parts = [
                "Based on the uploaded document context, here is a grounded response.",
                "",
                f"Summary: {base_answer}",
                "",
                "Key document-backed points:",
            ]
            response_parts.extend([f"- {line}" for line in context_lines])
            response_parts.append("")
            response_parts.append(
                "Recommendation: Use the cited document extracts for formal review, and verify section-wise applicability before final filing or advisory use."
            )
            response_text = "\n".join(response_parts)
            confidence = 0.86
        else:
            response_text = (
                f"{base_answer}\n\n"
                "No relevant uploaded document context was available for this answer, so treat it as a general guidance response and verify it against the applicable law, circular, or working papers."
            )
            confidence = 0.68

        return {
            "response": response_text,
            "confidence": confidence,
            "sources_used": bool(context_lines),
            "model": self.model_name + " (Grounded Local)",
        }
    
    def generate_response(
        self,
        query: str,
        context: str = "",
        system_prompt: str = None
    ) -> dict:
        """
        Generate response with context to avoid hallucinations
        
        Args:
            query: User query
            context: Relevant context from RAG
            system_prompt: System instructions
        
        Returns:
            {
                "response": str,
                "confidence": float,
                "sources_used": bool,
                "model": str
            }
        """
        
        if self.provider in ["auto", "ollama"]:
            ollama_result = self._generate_ollama_response(query, context, system_prompt)
            if ollama_result is not None:
                return ollama_result

        if self.provider in ["auto", "huggingface"]:
            huggingface_result, huggingface_error = self._huggingface_chat(
                query,
                context,
                system_prompt,
            )
            if huggingface_result is not None:
                return huggingface_result
            if huggingface_error:
                self.last_ollama_error = huggingface_error

        if self.client is None:
            fallback = self._build_grounded_response(query, context)
            if self.last_ollama_error:
                fallback["error"] = self.last_ollama_error
            return fallback
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self._build_messages(query, context, system_prompt),
                temperature=self.temperature,
                max_tokens=2048
            )
            
            generated_text = response.choices[0].message.content
            if not generated_text:
                return self._build_grounded_response(query, context)
            
            return {
                "response": generated_text,
                "confidence": 0.85 if context else 0.6,  # Higher confidence with context
                "sources_used": bool(context),
                "model": self.model_name,
                "finish_reason": response.choices[0].finish_reason
            }
        
        except Exception as e:
            fallback = self._build_grounded_response(query, context)
            fallback["error"] = str(e)
            return fallback
    
    def _generate_mock_response(self, query: str, context: str = "") -> dict:
        """Generate mock response for testing without OpenAI"""
        return self._build_grounded_response(query, context)
    
    def extract_citations(self, response: str, sources: List[dict]) -> List[dict]:
        """Extract citations from response based on sources"""
        citations = []
        
        for source in sources:
            citations.append({
                "document_name": source.get("doc_name", "Unknown"),
                "chunk_index": source.get("chunk_index", 0),
                "similarity": source.get("similarity", 0),
                "section": f"Section {source.get('chunk_index')}"
            })
        
        return citations


# Global LLM service
llm_service = None

def init_llm_service(
    api_key: str = None,
    model_name: str = "gpt-4",
    provider: str = "auto",
    huggingface_api_key: str = None,
    huggingface_model: str = "openai/gpt-oss-20b:cheapest",
    huggingface_base_url: str = "https://router.huggingface.co/v1/chat/completions",
    ollama_base_url: str = "http://127.0.0.1:11434",
    ollama_model: str = "qwen2.5:1.5b-instruct",
    ollama_fallback_models: Optional[List[str]] = None,
):
    """Initialize LLM service"""
    global llm_service
    llm_service = LLMService(
        api_key=api_key,
        model_name=model_name,
        provider=provider,
        huggingface_api_key=huggingface_api_key,
        huggingface_model=huggingface_model,
        huggingface_base_url=huggingface_base_url,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_fallback_models=ollama_fallback_models,
    )
    return llm_service

def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    from app.core.config import settings

    global llm_service
    if llm_service is None:
        llm_service = LLMService(
            api_key=settings.openai_api_key,
            model_name=settings.model_name,
            provider=settings.llm_provider,
            huggingface_api_key=settings.huggingface_api_key,
            huggingface_model=settings.huggingface_model,
            huggingface_base_url=settings.huggingface_base_url,
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
            ollama_fallback_models=[
                model.strip()
                for model in settings.ollama_fallback_models.split(",")
                if model.strip()
            ],
        )
    return llm_service
