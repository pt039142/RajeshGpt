"""RajeshGPT Streamlit frontend."""

from datetime import datetime
import html
import os

import PyPDF2
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("RAJESHGPT_BACKEND_URL", "http://127.0.0.1:8000")


def normalize_text(text):
    text = "" if text is None else str(text)
    for old, new in {
        "â‚¹": "Rs. ",
        "â‰¤": "<=",
        "â‰¥": ">=",
        "â€¢": "-",
    }.items():
        text = text.replace(old, new)
    return text.strip()


def escape_html_text(text):
    return html.escape(normalize_text(text)).replace("\n", "<br>")


def extract_pdf_text(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, len(reader.pages)
    except Exception as exc:
        st.error(f"Error reading PDF: {exc}")
        return None, 0


def validate_query(query):
    query_lower = query.lower()
    in_scope = [
        "income tax", "itr", "deduction", "80c", "80d", "80e", "tds", "gst",
        "capital gains", "salary", "audit", "accounting", "company", "llp",
        "compliance", "form 16", "assessment", "ca", "chartered accountant",
    ]
    out_scope = ["medical", "travel", "visa", "sports", "weather", "crypto"]
    in_hits = sum(1 for item in in_scope if item in query_lower)
    out_hits = sum(1 for item in out_scope if item in query_lower)
    if out_hits and not in_hits:
        return {
            "is_valid": False,
            "confidence": 0.9,
            "scope": "out_of_scope",
            "reason": "Question appears outside tax, finance, or CA workflows.",
            "warnings": [],
        }
    warnings = []
    if len(query.strip()) < 10:
        warnings.append("Add more context for a stronger answer.")
    return {
        "is_valid": True,
        "confidence": min(0.95, 0.65 + in_hits * 0.08) if in_hits else 0.7,
        "scope": "in_scope",
        "reason": "Question fits tax, compliance, or finance support.",
        "warnings": warnings,
    }


def get_tax_knowledge(query):
    query_lower = query.lower()
    data = {
        "80c": "Section 80C generally allows deduction up to Rs. 1,50,000 for eligible investments and payments such as PF, PPF, ELSS, life insurance premium, and certain principal repayments.",
        "80d": "Section 80D generally covers health insurance premium deduction for self, family, and parents, with higher limits for senior citizens.",
        "80e": "Section 80E generally covers deduction of eligible education loan interest for up to eight assessment years, subject to conditions.",
        "tds": "TDS is tax deducted at source. The rate depends on the nature of payment such as salary, interest, rent, commission, or professional fees.",
        "gst": "GST is a destination-based indirect tax on supply of goods and services. Registration, rates, and return duties depend on turnover and business type.",
        "form 16": "Form 16 is the employer-issued TDS certificate for salary income and is commonly used while preparing income tax returns.",
        "capital gains": "Capital gains tax treatment depends on asset class, holding period, and whether the gain is short-term or long-term.",
        "company": "Company tax analysis usually covers income classification, expenses, depreciation, audit, compliance dates, and filing duties.",
        "audit": "Audit and tax review work generally checks records, compliance, evidence quality, and whether tax positions are properly supported.",
        "default": "RajeshGPT is focused on Indian income tax, business taxation, compliance, and CA workflows. Upload supporting PDFs and ask a specific question for a stronger result.",
    }
    for key, value in data.items():
        if key != "default" and key in query_lower:
            return value
    return data["default"]


def generate_response(query, selected_docs, documents):
    validation = validate_query(query)
    notes = []
    citations = []
    for name in selected_docs:
        if name not in documents:
            continue
        lines = [line.strip() for line in documents[name]["text"].split(".") if line.strip()]
        hits = [line for line in lines if any(word in line.lower() for word in query.lower().split())][:2]
        if hits:
            notes.append(f"From {name}: " + ". ".join(hits))
            citations.append(f"{name} - {documents[name]['pages']} pages")
    answer = get_tax_knowledge(query)
    if notes:
        answer += "\n\nDocument-backed notes:\n- " + "\n- ".join(normalize_text(note) for note in notes)
    else:
        answer += "\n\nNo supporting document was selected for this answer."
    return {
        "answer": normalize_text(answer),
        "citations": [normalize_text(item) for item in citations],
        "confidence": validation["confidence"],
        "scope": validation["scope"],
        "has_risk": not citations,
    }


def api_get(path, params=None):
    try:
        response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=20)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:
        return None, str(exc)


def api_post_json(path, payload):
    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=60)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:
        return None, str(exc)


def api_post_file(path, uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        files = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
        response = requests.post(f"{BACKEND_URL}{path}", files=files, timeout=120)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:
        return None, str(exc)


def info_card(title, body, tone="neutral"):
    st.markdown(
        f"<div class='card {tone}'><div class='card-title'>{escape_html_text(title)}</div><div class='card-copy'>{escape_html_text(body)}</div></div>",
        unsafe_allow_html=True,
    )


def message_card(role, content):
    label = "RajeshGPT" if role == "assistant" else "You"
    cls = "assistant" if role == "assistant" else "user"
    st.markdown(
        f"<div class='msg {cls}'><div class='msg-role'>{label}</div><div class='msg-copy'>{escape_html_text(content)}</div></div>",
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="RajeshGPT - Tax Workspace", page_icon="RG", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Merriweather:wght@700&display=swap');
    :root { --ink:#132229; --muted:#5f6c72; --deep:#12343b; --gold:#c6a76a; --line:rgba(18,52,59,.12); }
    html,body,[class*="css"] { font-family:'Manrope',sans-serif; color:var(--ink); }
    .stApp { background:linear-gradient(180deg,#efe6d6 0%,#f8f4ec 22%,#fbfaf7 100%); }
    .main .block-container { max-width:1200px; padding-top:1.4rem; }
    h1,h2,h3 { font-family:'Merriweather',serif; color:var(--deep); }
    .hero { background:linear-gradient(135deg,#12343b 0%,#1d4e57 70%,#c6a76a 100%); color:#fff8ed; padding:2rem; border-radius:28px; box-shadow:0 24px 64px rgba(18,32,39,.12); margin-bottom:1rem; }
    .hero-kicker { font-size:.78rem; text-transform:uppercase; letter-spacing:.18em; font-weight:800; opacity:.82; }
    .hero-title { font-family:'Merriweather',serif; font-size:2.8rem; line-height:1.08; margin:.5rem 0; max-width:720px; }
    .hero-copy { max-width:760px; line-height:1.7; }
    .chip { display:inline-block; margin:.35rem .45rem 0 0; padding:.5rem .9rem; border-radius:999px; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.16); }
    .panel { background:rgba(255,255,255,.84); border:1px solid rgba(255,255,255,.85); border-radius:22px; padding:1.1rem; box-shadow:0 18px 44px rgba(18,32,39,.08); margin-bottom:1rem; }
    .metricbox { background:rgba(255,255,255,.76); border:1px solid var(--line); border-radius:18px; padding:1rem; min-height:112px; }
    .metriclabel { font-size:.76rem; text-transform:uppercase; letter-spacing:.14em; color:var(--muted); font-weight:800; }
    .metricvalue { font-size:1.9rem; color:var(--deep); font-weight:800; margin:.4rem 0; }
    .metriccopy { color:var(--muted); font-size:.9rem; }
    .card { border-radius:18px; border:1px solid var(--line); padding:1rem; margin-bottom:.75rem; background:rgba(255,255,255,.9); }
    .card-title { font-weight:800; color:var(--deep); margin-bottom:.35rem; }
    .card-copy { color:var(--muted); line-height:1.6; }
    .neutral { border-left:5px solid var(--gold); }
    .success { border-left:5px solid #2f7d4a; }
    .warning { border-left:5px solid #b67a1f; }
    .danger { border-left:5px solid #a63c34; }
    .msg { border-radius:20px; padding:1rem 1.1rem; margin-bottom:.9rem; border:1px solid var(--line); }
    .msg.user { background:linear-gradient(135deg,rgba(18,52,59,.08),rgba(198,167,106,.18)); }
    .msg.assistant { background:rgba(255,255,255,.94); }
    .msg-role { font-size:.76rem; text-transform:uppercase; letter-spacing:.14em; color:var(--muted); font-weight:800; margin-bottom:.45rem; }
    .msg-copy { line-height:1.7; }
    .stTabs [data-baseweb="tab-list"] { gap:.45rem; background:rgba(255,255,255,.66); border:1px solid rgba(255,255,255,.86); border-radius:18px; padding:.35rem; }
    .stTabs [data-baseweb="tab"] { height:50px; border-radius:14px; font-weight:700; }
    .stTabs [aria-selected="true"] { background:linear-gradient(135deg,#12343b 0%,#1d4e57 100%); color:#fff8ed !important; }
    .stButton > button { width:100%; min-height:3rem; border-radius:14px; border:none; font-weight:800; background:linear-gradient(135deg,#12343b 0%,#1d4e57 100%); color:#fff8ed; }
    .stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"] > div,.stMultiSelect div[data-baseweb="select"] > div,.stFileUploader { border-radius:14px !important; border:1px solid var(--line) !important; background:rgba(255,255,255,.92) !important; }
    .stSidebar { background:linear-gradient(180deg,#12343b 0%,#1b4850 100%); }
    .stSidebar,.stSidebar p,.stSidebar label,.stSidebar span,.stSidebar div { color:#edf3ef; }
    .stSidebar h1,.stSidebar h2,.stSidebar h3 { color:#fff8ed; font-family:'Merriweather',serif; }
    .footer { text-align:center; color:#5f6c72; padding:.75rem 0 .25rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

for key, default in {
    "documents": {},
    "conversation_history": [],
    "uploaded_files": {},
    "backend_status": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

health_data, health_error = api_get("/api/health")
st.session_state.backend_status = {
    "online": health_error is None,
    "details": health_data if health_data else {},
    "error": health_error,
}

with st.sidebar:
    st.markdown("## RajeshGPT Control")
    info_card("Audience", "Built for directors, tax officers, chartered accountants, and finance teams.", "neutral")
    if st.session_state.backend_status["online"]:
        info_card("Backend status", "Connected to FastAPI backend.", "success")
    else:
        info_card("Backend status", "Backend is offline. The UI will use local fallback responses until the API is running.", "warning")
    confidence_threshold = st.slider("Confidence threshold", 0.0, 1.0, 0.7, 0.1)
    show_citations = st.checkbox("Show citations", value=True)
    auto_validate = st.checkbox("Auto-validate queries", value=True)
    model_choice = st.selectbox("Model profile", ["Mock knowledge base", "Mistral 7B", "DistilGPT-2", "GPT-4", "GPT-3.5 Turbo"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    info_card("Deployment note", "Use document-backed answers, low temperature, and citations for formal workflows.", "warning")
    if st.button("Clear all session data", use_container_width=True):
        st.session_state.documents = {}
        st.session_state.conversation_history = []
        st.session_state.uploaded_files = {}
        st.success("Session data cleared.")

st.markdown(
    f"""
    <div class='hero'>
      <div class='hero-kicker'>Trusted Tax Intelligence Workspace</div>
      <div class='hero-title'>A cleaner RajeshGPT frontend for executive tax and CA work.</div>
      <div class='hero-copy'>This UI is designed to feel credible in front of a Director of Income Tax, practical for chartered accountants, and simple enough for everyday staff use.</div>
      <div class='chip'>{len(st.session_state.documents)} active documents</div>
      <div class='chip'>{len(st.session_state.conversation_history)} conversation entries</div>
      <div class='chip'>{escape_html_text(model_choice)}</div>
      <div class='chip'>Confidence floor {confidence_threshold:.0%}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='metricbox'><div class='metriclabel'>UX goal</div><div class='metricvalue'>Clear</div><div class='metriccopy'>Cleaner hierarchy and easier navigation.</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metricbox'><div class='metriclabel'>Trust goal</div><div class='metricvalue'>Grounded</div><div class='metriccopy'>Confidence, scope, and citations remain visible.</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metricbox'><div class='metriclabel'>Deployment goal</div><div class='metricvalue'>Ready</div><div class='metriccopy'>Stronger presentation for demos and rollout.</div></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Chat workspace", "Document vault", "Query validator", "About platform"])

with tab1:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### Advisory workspace")
    st.caption("Use this for deduction analysis, filing guidance, document-backed summaries, and CA review support.")
    in1, in2 = st.columns([4, 1])
    with in1:
        query = st.text_input("Question", placeholder="Example: Summarize Section 80C deductions for a salaried taxpayer.", label_visibility="collapsed")
    with in2:
        submit_btn = st.button("Generate response", use_container_width=True)
    if st.session_state.documents:
        selected_docs = st.multiselect("Use uploaded documents as ground truth", list(st.session_state.documents.keys()))
    else:
        selected_docs = []
        info_card("No source documents selected", "Upload circulars, return forms, or assessment orders for stronger answers.", "warning")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.conversation_history:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Conversation")
        for item in st.session_state.conversation_history:
            message_card(item["role"], item["content"])
            if item["role"] == "assistant":
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Confidence", f"{item['confidence']:.0%}")
                with m2:
                    st.metric("Scope", item["scope"].replace("_", " ").title())
                with m3:
                    st.metric("Reliability", "Needs verification" if item["has_risk"] else "Ready to use")
                if show_citations and item["citations"]:
                    with st.expander("Source citations"):
                        for cite in item["citations"]:
                            st.write(f"- {cite}")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        info_card("Executive presentation", "A cleaner interface suitable for stakeholder demos and internal review.", "neutral")
        info_card("Tax and CA productivity", "Faster access to tax guidance, compliance topics, and document-backed notes.", "success")
        info_card("Safer answers", "Out-of-scope prompts are flagged and document support is visible.", "warning")
        st.markdown("</div>", unsafe_allow_html=True)

    if submit_btn and query:
        validation = validate_query(query)
        if st.session_state.backend_status["online"]:
            api_validation, api_validation_error = api_get("/api/query/validate", {"query": query})
            if api_validation and api_validation.get("validation"):
                validation = api_validation["validation"]
        if auto_validate and not validation["is_valid"]:
            info_card("Query outside supported scope", validation["reason"], "danger")
        else:
            st.session_state.conversation_history.append({"role": "user", "content": normalize_text(query)})
            with st.spinner("Analyzing the query and preparing a response..."):
                response = None
                if st.session_state.backend_status["online"]:
                    selected_doc_ids = [
                        st.session_state.documents[name]["backend_id"]
                        for name in selected_docs
                        if name in st.session_state.documents and st.session_state.documents[name].get("backend_id") is not None
                    ]
                    api_response, api_response_error = api_post_json(
                        "/api/query",
                        {
                            "query": query,
                            "document_ids": selected_doc_ids,
                        },
                    )
                    if api_response and api_response.get("success") and api_response.get("data"):
                        data = api_response["data"]
                        response = {
                            "answer": normalize_text(data.get("response", "")),
                            "citations": [
                                normalize_text(
                                    f"{cite.get('document_name', 'Document')} - {cite.get('section', '')}"
                                )
                                for cite in data.get("citations", [])
                            ],
                            "confidence": data.get("confidence_score", validation["confidence"]),
                            "scope": data.get("scope", validation["scope"]),
                            "has_risk": data.get("has_hallucination_risk", False),
                        }
                    elif api_response and not api_response.get("success"):
                        info_card("Backend response", api_response.get("message", "Unable to process query."), "warning")
                    elif api_response_error:
                        info_card("Backend connection issue", api_response_error, "warning")

                if response is None:
                    response = generate_response(query, selected_docs, st.session_state.documents)
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": response["answer"],
                "citations": response["citations"],
                "confidence": response["confidence"],
                "scope": response["scope"],
                "has_risk": response["has_risk"],
            })
            if response["confidence"] < confidence_threshold:
                info_card("Response below preferred confidence threshold", "Upload better supporting documents or narrow the question before formal use.", "warning")
            st.rerun()

with tab2:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### Document vault")
    st.caption("Upload PDFs that should act as authoritative context.")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        if uploaded_file.size > 50 * 1024 * 1024:
            st.error("File too large. Maximum supported size is 50 MB.")
        else:
            text, pages = extract_pdf_text(uploaded_file)
            backend_id = None
            if st.session_state.backend_status["online"]:
                upload_response, upload_error = api_post_file("/api/documents/upload", uploaded_file)
                if upload_response and upload_response.get("success") and upload_response.get("data"):
                    backend_id = upload_response["data"].get("id")
                elif upload_error:
                    info_card("Backend upload issue", upload_error, "warning")
            if text:
                st.session_state.documents[uploaded_file.name] = {
                    "text": text,
                    "pages": pages,
                    "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "size": uploaded_file.size / 1024 / 1024,
                    "backend_id": backend_id,
                }
                info_card("Document added", f"{uploaded_file.name} is now available for future answers.", "success")
    if st.session_state.documents:
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Documents", len(st.session_state.documents))
        with s2:
            st.metric("Total pages", sum(doc["pages"] for doc in st.session_state.documents.values()))
        with s3:
            st.metric("Total size (MB)", f"{sum(doc['size'] for doc in st.session_state.documents.values()):.2f}")
        for name, doc in st.session_state.documents.items():
            backend_note = " | Synced to backend" if doc.get("backend_id") is not None else " | Local only"
            info_card(name, f"Pages: {doc['pages']} | Size: {doc['size']:.2f} MB | Uploaded: {doc['uploaded_at']}{backend_note}", "neutral")
            with st.expander(f"Preview: {name}"):
                st.text(normalize_text(doc["text"][:700]) + "...")
    else:
        info_card("Vault is empty", "Add PDFs here to improve trust and answer quality.", "warning")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### Query validator")
    test_query = st.text_area("Enter a query to validate", placeholder="Example: Can a taxpayer claim home loan interest and Section 80C deduction together?", height=120)
    if st.button("Validate query"):
        if test_query:
            result = validate_query(test_query)
            if st.session_state.backend_status["online"]:
                api_result, api_error = api_get("/api/query/validate", {"query": test_query})
                if api_result and api_result.get("validation"):
                    result = api_result["validation"]
            v1, v2, v3 = st.columns(3)
            with v1:
                st.metric("Valid", "Yes" if result["is_valid"] else "No")
            with v2:
                st.metric("Confidence", f"{result['confidence']:.0%}")
            with v3:
                st.metric("Scope", result["scope"].replace("_", " ").title())
            info_card("Classifier analysis", result["reason"], "success" if result["is_valid"] else "danger")
            for warning in result["warnings"]:
                info_card("Refinement suggestion", warning, "warning")
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### About platform")
    info_card("Who this UI serves", "Directors, commissioners, tax officers, CAs, finance teams, and users who need dependable tax assistance with a polished look.", "neutral")
    info_card("Core strengths", "Document upload, scope validation, confidence display, and citation support.", "success")
    info_card("Next production step", "Connect this frontend to the backend API, add authentication, persistent storage, and audit logging.", "warning")
    st.json({
        "app_name": "RajeshGPT",
        "version": "1.1.0",
        "type": "Streamlit tax workspace",
        "audience": "Income Tax leadership, officers, CAs, finance professionals",
        "deployment_status": "UI refreshed, backend integration recommended",
    })
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>RajeshGPT v1.1.0 | Professional income tax guidance workspace</div>", unsafe_allow_html=True)
