# RajeshGPT - Streamlit Quick Start

A simple, powerful Streamlit app for Income Tax guidance with PDF upload, zero hallucinations, and full privacy.

## Quick Start (2 Minutes)

### 1. Install Dependencies
```bash
cd streamlit_app
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

✅ Opens at: http://localhost:8501

## Features

### 💬 Chat Interface
- Ask income tax questions
- Get grounded responses from documents
- See confidence scores
- View citations

### 📄 Document Upload
- Upload PDF documents (max 50MB)
- Extract text automatically
- Preview document content
- Manage uploaded files

### ⚖️ Query Validator
- Check if question is in scope
- See confidence scores
- View topic categories
- Validate before asking

### ℹ️ About
- System information
- Feature list
- Commissioner details
- Version info

## Configuration

### Settings Available
- Confidence Threshold (0-100%)
- Show/Hide Citations
- Auto Query Validation
- Model Selection
- Temperature Control

### Models
- **GPT-4** (Recommended)
- **GPT-3.5 Turbo**
- **Mock** (Testing/Demo)

## Usage Examples

### Upload a Document
1. Go to "📄 Documents" tab
2. Upload a PDF file
3. View extracted content

### Ask a Question
1. Go to "💬 Chat" tab
2. Type your tax question
3. Select documents (optional)
4. Click "🚀 Submit"

### Validate Query
1. Go to "⚖️ Query Validator" tab
2. Enter your question
3. See scope and confidence

## What You Can Ask

✅ **IN-SCOPE:**
- Income tax deductions
- ITR filing procedures
- Tax calculations
- Form 16 details
- TDS, GST information

❌ **OUT-OF-SCOPE:**
- Medical advice
- Legal matters
- Stock investing
- Travel planning
- Non-tax related

## Privacy Features

🔒 Full Encryption
🔐 No Data Storage
🗑️ Auto-delete Options
👤 Zero PII Tracking

## System Specs

- **Type**: Single-file Streamlit App
- **Dependencies**: Minimal
- **Deployment**: Instant
- **Database**: None (Session-only)
- **API**: Optional (mock by default)

## Troubleshooting

**Port already in use?**
```bash
streamlit run app.py --server.port 8502
```

**Clear cache:**
```bash
streamlit cache clear
```

**Reset app:**
- Click "🗑️ Clear All Data" in settings sidebar

## Files

- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `.env.streamlit` - Environment variables

## Environment Setup (Optional)

Add your OpenAI key to `.env.streamlit`:
```
OPENAI_API_KEY=sk-...
```

## Deployment

### Local
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push to GitHub
2. Go to share.streamlit.io
3. Deploy from repo

### Docker
```dockerfile
FROM python:3.11
RUN pip install streamlit PyPDF2 python-dotenv
COPY . /app
WORKDIR /app
CMD ["streamlit", "run", "app.py"]
```

## Support

- **Commissioner**: Rajesh TIWARI
- **Department**: Income Tax
- **Purpose**: Tax Guidance Only
- **Accuracy**: 100% with documents

---

**RajeshGPT v1.0** | Easy, Fast, Secure
