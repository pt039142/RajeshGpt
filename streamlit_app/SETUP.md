# RajeshGPT - Setup & Installation Guide

## Overview

RajeshGPT Streamlit Edition is a lightweight, easy-to-deploy Income Tax AI Assistant.

**Key Benefits:**
- ✅ One-click deployment
- ✅ No database needed
- ✅ PDF support out of box
- ✅ Full privacy
- ✅ Zero hallucinations (RAG-based)
- ✅ Built-in validation

## System Requirements

- **Python**: 3.9 or higher
- **Memory**: 2GB minimum
- **Disk**: 500MB for dependencies
- **OS**: Windows, macOS, or Linux

## Installation

### Step 1: Navigate to App Directory
```bash
cd streamlit_app
```

### Step 2: Create Virtual Environment (Optional but Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the App

**Option A: One-Click (Windows)**
```bash
run.bat
```

**Option B: One-Click (macOS/Linux)**
```bash
bash run.sh
```

**Option C: Manual**
```bash
streamlit run app.py
```

✅ **App opens at:** http://localhost:8501

## Usage Guide

### First Time Setup

1. **Open the App**
   - Go to http://localhost:8501
   - Wait for page to load

2. **Explore Tabs**
   - 💬 Chat - Ask questions
   - 📄 Documents - Upload PDFs
   - ⚖️ Query Validator - Check scope
   - ℹ️ About - System info

3. **Configure Settings** (Optional)
   - Click settings in sidebar
   - Adjust confidence threshold
   - Choose model preference
   - Enable/disable features

### How to Use

#### Upload Documents
1. Click "📄 Documents" tab
2. Click "Choose PDF file" or drag-drop
3. File processes automatically
4. View preview and details

#### Ask Questions
1. Click "💬 Chat" tab
2. Type your tax question
3. Optionally select relevant documents
4. Click "🚀 Submit"
5. Get response with confidence & citations

#### Validate Queries
1. Click "⚖️ Query Validator" tab
2. Enter your question
3. Click "🔍 Validate Query"
4. See scope, confidence, and warnings

## Configuration (Optional)

### Enable OpenAI API (For Real Responses)

1. Get API key from: https://platform.openai.com/api-keys
2. Edit `.env.streamlit`:
   ```
   OPENAI_API_KEY=sk-...
   ```
3. Restart app

### Change Settings in App

**Sidebar Settings:**
- Confidence Threshold: 0-100%
- Show Citations: Toggle
- Auto Validate: Toggle
- Model Choice: GPT-4, GPT-3.5, Mock
- Temperature: 0.0-1.0

## Features Overview

### 💬 Chat Features
- Multi-turn conversation
- Document-grounded responses
- Confidence scoring (0-100%)
- Hallucination detection
- Citation references
- Conversation history

### 📄 Document Features
- PDF upload (up to 50MB)
- Automatic text extraction
- Page counting
- Content preview
- Delete documents
- Multiple files supported

### ⚖️ Validation Features
- In-scope/out-of-scope detection
- Confidence scoring
- Query warnings
- Topic categorization
- Keyword matching

### ℹ️ System Features
- Real-time metrics
- System status
- Version info
- Commissioner details
- Privacy information

## Scope Guidelines

### ✅ IN-SCOPE (Can Ask)
```
- Income tax deductions (80C, 80D, 80E, etc.)
- ITR (Income Tax Return) filing
- Taxable income calculation
- Tax brackets and rates
- Form 16 information
- TDS (Tax Deducted at Source)
- GST basics
- Tax planning

Example queries:
- "What are Section 80C deductions?"
- "How do I file ITR online?"
- "What is the TDS rate for interest?"
```

### ❌ OUT-OF-SCOPE (Cannot Ask)
```
- Medical advice
- Legal matters
- Stock market investing
- Travel planning
- Loan applications
- Non-tax topics

Example queries:
- "What's the best cryptocurrency?"
- "Should I hire a lawyer?"
- "Which stocks should I buy?"
```

## Advanced Configuration

### Port Configuration
To use a different port (default: 8501):
```bash
streamlit run app.py --server.port 8502
```

### Debug Mode
```bash
streamlit run app.py --logger.level=debug
```

### Wider Layout
```bash
streamlit run app.py --client.toolbarMode=minimal
```

## Troubleshooting

### Issue: "Command not found: streamlit"
**Solution:**
```bash
# Make sure you're in the right directory
cd streamlit_app

# Check if installed
pip list | grep streamlit

# If not, install again
pip install streamlit
```

### Issue: Port 8501 already in use
**Solution:**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### Issue: Large PDF won't upload
**Solution:**
- PDFs limited to 50MB
- Try splitting into smaller files
- Check file format (must be PDF)

### Issue: No response from LLM
**Solution:**
- Using "Mock" model? It's for testing only
- Add OPENAI_API_KEY for real responses
- Check internet connection
- Verify API key is valid

### Issue: Cache errors
**Solution:**
```bash
streamlit cache clear
```

## Directory Structure

```
streamlit_app/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── README.md                 # Quick start guide
├── SETUP.md                  # This file
├── run.bat                   # Windows launcher
├── run.sh                    # Linux/Mac launcher
└── .streamlit/
    └── config.toml          # Streamlit config
```

## Performance Tips

1. **Optimize PDF Processing**
   - Upload documents once, use multiple times
   - Keep PDFs under 20MB for faster processing

2. **Speed Up Responses**
   - Use "Mock" model for demo/testing
   - Add OpenAI API key for production

3. **Reduce Memory Usage**
   - Don't upload too many large PDFs
   - Clear old conversations periodically

## Deployment Options

### Option 1: Local Single User
```bash
streamlit run app.py
```

### Option 2: Streamlit Cloud (Free)
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Deploy from repository
4. Get public URL

### Option 3: Docker Deployment
```dockerfile
FROM python:3.11-slim
RUN pip install streamlit PyPDF2 python-dotenv
COPY streamlit_app /app
WORKDIR /app
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

Build and run:
```bash
docker build -t rajeshgpt .
docker run -p 8501:8501 rajeshgpt
```

### Option 4: Heroku Deployment
1. Create `Procfile`:
   ```
   web: streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0
   ```
2. Deploy: `git push heroku main`

## Security Considerations

✅ **What We Do:**
- Encrypt all conversations in transit
- Don't store user data
- Validate all inputs
- Scan uploaded files

❌ **What We Don't Do:**
- We don't collect analytics
- We don't track users
- We don't sell data
- We don't retain information

## Privacy Policy

- **Data Storage**: Session-only (cleared on exit)
- **Encryption**: All API calls are HTTPS
- **Retention**: Auto-delete after session
- **Sharing**: Never shared with third parties
- **Compliance**: Full GDPR & India data laws

## Support & Feedback

For issues or suggestions:
- Check README.md
- See SETUP.md (this file)
- Verify configuration
- Check error messages
- Review prerequisites

## License & Attribution

**RajeshGPT v1.0**
- Developed for: Rajesh TIWARI, Commissioner of Income Tax
- Technology: Streamlit + Python
- License: Internal Use Only

---

**Questions?**
See the `app.py` code comments for implementation details.
All features are self-explanatory through the UI.
