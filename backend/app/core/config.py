"""Configuration settings for RajeshGPT"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "RajeshGPT - Income Tax Assistant"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    api_title: str = "RajeshGPT API"
    api_description: str = "LLM-based Income Tax Assistant with Zero Hallucinations"
    api_version: str = "1.0.0"
    
    # Security & Privacy
    secret_key: str = os.getenv("SECRET_KEY", "rajeshgpt-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    
    # LLM Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = "gpt-4"
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
    ollama_fallback_models: str = os.getenv(
        "OLLAMA_FALLBACK_MODELS",
        "qwen2.5:1.5b-instruct,qwen2.5:0.5b-instruct",
    )
    temperature: float = 0.3  # Lower for more deterministic responses
    max_tokens: int = 2048
    
    # Vector DB (Pinecone)
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_env: str = os.getenv("PINECONE_ENV", "")
    pinecone_index: str = "rajeshgpt-income-tax"
    
    # PDF Processing
    max_pdf_size_mb: int = 50
    allowed_pdf_formats: list = ["pdf"]
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./rajeshgpt.db"
    )
    
    # Redis for caching
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File Upload
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    embeddings_dir: str = os.getenv("EMBEDDINGS_DIR", "./embeddings")
    
    # System Prompts
    system_prompt: str = """You are RajeshGPT, an AI assistant for Indian income tax, finance, accounting, compliance, business operations, and chartered accountancy workflows.
You are commissioned for professional-quality assistance suitable for officers, directors, reviewers, finance teams, and CA teams.

CRITICAL RULES:
1. NO HALLUCINATIONS: Prefer uploaded documents and grounded context whenever available.
2. FINANCE-FIRST SCOPE: You may answer tax, GST, TDS, accounting, audit, business finance, brokers, stock exchanges, listed companies, company law-adjacent compliance, and CA workflow questions.
3. PRIVACY FIRST: Never expose or retain sensitive personal information beyond the current task.
4. ACCURACY: If the answer depends on a specific document or law text that is missing, say what is missing instead of pretending certainty.
5. CITATIONS: When documents are available, ground the answer in those documents and cite them.
6. TONE: Answer in a professional, concise, practical style suitable for work use.
7. GENERAL BUSINESS QUESTIONS: If the user asks about a company, exchange, broker, finance concept, or greeting, answer directly and helpfully. Do not reject those questions merely because they are not purely tax questions.
"""

    # Scope Keywords (for validation)
    in_scope_keywords: list = [
        "income tax", "itr", "deduction", "taxable income", "tax bracket",
        "capital gains", "dividend", "salary", "business income", "return",
        "form 16", "tds", "gst", "tax planning", "tax filing", "assessment",
        "finance", "financial", "accounting", "account", "audit", "bookkeeping",
        "balance sheet", "cash flow", "p&l", "profit and loss", "working capital",
        "ratio", "compliance", "company tax", "corporate tax", "llp", "partnership",
        "chartered accountant", "ca", "notice", "section", "rebate", "business",
        "invoice", "expense", "revenue", "depreciation"
    ]
    
    out_of_scope_keywords: list = [
        "cryptocurrency", "bitcoin", "investment advice",
        "loan application", "visa", "travel", "legal case", "medical"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
