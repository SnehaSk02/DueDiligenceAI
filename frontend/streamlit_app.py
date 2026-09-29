import streamlit as st
import requests
from typing import Dict,Any,List 
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="DueDiligenceAI",page_icon="🔎", layout="wide", initial_sidebar_state="expanded")

# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* =========================
       GLOBAL BACKGROUND
       ========================= */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(99, 102, 241, 0.18),
                transparent 30%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(236, 72, 153, 0.14),
                transparent 30%
            ),
            radial-gradient(
                circle at 50% 100%,
                rgba(14, 165, 233, 0.10),
                transparent 35%
            ),
            #080b14;

        color: #f8fafc;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }


    /* =========================
       SIDEBAR
       ========================= */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #0b1020 0%,
                #111827 55%,
                #0b1020 100%
            );

        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb;
    }


    /* =========================
       HERO
       ========================= */

    .hero {
        padding: 2.2rem 2.4rem;
        border-radius: 24px;
        margin-bottom: 1.8rem;

        background:
            linear-gradient(
                135deg,
                rgba(79,70,229,0.95),
                rgba(126,34,206,0.88),
                rgba(219,39,119,0.85)
            );

        box-shadow:
            0 20px 60px rgba(79,70,229,0.20);

        border: 1px solid rgba(255,255,255,0.12);
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        color: white;
        margin-bottom: 0.3rem;
    }

    .hero-subtitle {
        font-size: 1.08rem;
        color: rgba(255,255,255,0.88);
        max-width: 850px;
        line-height: 1.6;
    }

    .hero-badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        margin-bottom: 0.8rem;

        border-radius: 999px;

        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.20);

        color: white;
        font-size: 0.82rem;
        font-weight: 700;
    }


    /* =========================
       SECTION HEADERS
       ========================= */

    .section-title {
        font-size: 1.55rem;
        font-weight: 750;
        color: #f8fafc;
        margin-top: 1.5rem;
        margin-bottom: 0.25rem;
    }

    .section-subtitle {
        color: #94a3b8;
        margin-bottom: 1rem;
    }


    /* =========================
       CARDS
       ========================= */

    .glass-card {
        background:
            linear-gradient(
                145deg,
                rgba(30,41,59,0.80),
                rgba(15,23,42,0.88)
            );

        border: 1px solid rgba(148,163,184,0.13);
        border-radius: 18px;

        padding: 1.25rem;

        box-shadow:
            0 12px 40px rgba(0,0,0,0.20);

        margin-bottom: 1rem;
    }

    .metric-card {
        background:
            linear-gradient(
                145deg,
                rgba(30,41,59,0.95),
                rgba(15,23,42,0.95)
            );

        border: 1px solid rgba(99,102,241,0.20);
        border-radius: 16px;

        padding: 1.1rem;

        min-height: 120px;
    }

    .metric-label {
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 1.65rem;
        font-weight: 800;
        margin-top: 0.3rem;
    }

    .metric-accent {
        color: #a5b4fc;
    }


    /* =========================
       STATUS BADGES
       ========================= */

    .status-success {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;

        background: rgba(34,197,94,0.12);
        border: 1px solid rgba(34,197,94,0.25);

        color: #86efac;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .status-warning {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;

        background: rgba(245,158,11,0.12);
        border: 1px solid rgba(245,158,11,0.25);

        color: #fcd34d;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .status-danger {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;

        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.25);

        color: #fca5a5;
        font-size: 0.78rem;
        font-weight: 700;
    }


    /* =========================
       REPORT
       ========================= */

    .report-section {
        background:
            linear-gradient(
                145deg,
                rgba(15,23,42,0.96),
                rgba(17,24,39,0.90)
            );

        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 18px;

        padding: 1.4rem 1.5rem;

        margin-bottom: 1rem;

        box-shadow:
            0 8px 30px rgba(0,0,0,0.16);
    }

    .report-heading {
        color: #c4b5fd;
        font-size: 1.25rem;
        font-weight: 750;
        margin-bottom: 0.65rem;
    }

    .report-text {
        color: #dbeafe;
        line-height: 1.75;
        font-size: 0.98rem;
    }


    /* =========================
       FINDINGS
       ========================= */

    .finding {
        background: rgba(59,130,246,0.08);
        border-left: 4px solid #60a5fa;

        padding: 0.85rem 1rem;
        margin-bottom: 0.7rem;

        border-radius: 0 10px 10px 0;

        color: #dbeafe;
        line-height: 1.55;
    }

    .red-flag {
        background: rgba(239,68,68,0.08);
        border-left: 4px solid #ef4444;

        padding: 0.85rem 1rem;
        margin-bottom: 0.7rem;

        border-radius: 0 10px 10px 0;

        color: #fecaca;
        line-height: 1.55;
    }


    /* =========================
       DOCUMENT CARDS
       ========================= */

    .document-card {
        background: rgba(15,23,42,0.80);
        border: 1px solid rgba(148,163,184,0.12);

        padding: 0.9rem;
        border-radius: 14px;

        margin-bottom: 0.7rem;
    }

    .document-name {
        color: #f8fafc;
        font-weight: 700;
        font-size: 0.94rem;
    }

    .document-type {
        color: #94a3b8;
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }


    /* =========================
       CHAT
       ========================= */

    .chat-answer {
        background:
            linear-gradient(
                145deg,
                rgba(30,41,59,0.90),
                rgba(15,23,42,0.95)
            );

        border: 1px solid rgba(99,102,241,0.18);

        border-radius: 16px;

        padding: 1.2rem;

        line-height: 1.7;

        color: #e2e8f0;
    }


    /* =========================
       BUTTONS
       ========================= */

    .stButton > button {
        border-radius: 12px;
        font-weight: 700;

        border: 1px solid rgba(255,255,255,0.10);

        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);

        border-color:
            rgba(129,140,248,0.50);

        box-shadow:
            0 8px 25px rgba(79,70,229,0.18);
    }


    /* =========================
       DIVIDER
       ========================= */

    .gradient-divider {
        height: 2px;
        border: none;

        background:
            linear-gradient(
                90deg,
                transparent,
                #6366f1,
                #ec4899,
                transparent
            );

        margin: 1.5rem 0;
    }


    /* =========================
       FOOTER
       ========================= */

    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.78rem;
        margin-top: 3rem;
        padding-top: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# SESSION STATE
# ============================================================

defaults = {
    "case_id": None,
    "company_name": "",
    "case_type": "Full Due Diligence",
    "documents": [],
    "report": None,
    "report_type": None,
    "report_sources": [],
    "retrieved_evidence": [],
    "report_metrics": {},
    "last_question": "",
    "last_answer": None,
    "last_sources": []
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value

# API HELPERS
# ============================================================

def api_post(
    endpoint: str,
    json: Dict[str, Any] | None = None,
    params: Dict[str, Any] | None = None,
    files=None
):

    try:

        response = requests.post(
            f"{API_URL}{endpoint}",
            json=json,
            params=params,
            files=files,
            timeout=180
        )
        print("DEBUG STATUS:", response.status_code)
        print("DEBUG RESPONSE:", response.text)

        if response.status_code >= 400:
            print("DEBUG: ABOUT TO RAISE ERROR")
            

            try:

                error_data = response.json()

                detail = error_data.get(
                    "detail",
                    error_data
                )

            except Exception:

                detail = response.text
            
            raise RuntimeError(str(detail))

        return response.json()

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to the FastAPI backend. "
            "Make sure FastAPI is running."
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "The request timed out. "
            "Report generation can take some time."
        )


def api_get(endpoint: str):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=30
        )

        if response.status_code >= 400:

            try:

                detail = response.json().get(
                    "detail",
                    response.text
                )

            except Exception:

                detail = response.text

            raise RuntimeError(str(detail))

        return response.json()

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to the FastAPI backend."
        )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">
            ✦ AI-POWERED INVESTMENT INTELLIGENCE
        </div>
        <div class="hero-title">
            🔎 DueDiligenceAI
        </div>
        <div class="hero-subtitle">
            Analyze company documents, retrieve evidence,
            identify risks, evaluate financial information,
            and generate grounded due-diligence reports
            using a multi-agent AI workflow.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# st.markdown(
#     """
#     <div style="
#         background: red;
#         color: white;
#         padding: 30px;
#         border-radius: 20px;
#         font-size: 30px;
#         font-weight: bold;
#     ">
#         🔎 DueDiligenceAI TEST
#     </div>
#     """,
#     unsafe_allow_html=True
# )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🔎 DueDiligenceAI")

    st.markdown(
        """
        <div style="
            color:#94a3b8;
            font-size:0.86rem;
            line-height:1.6;
            margin-bottom:1rem;
        ">

        Production-oriented AI due diligence platform
        using document RAG, specialist agents,
        LangGraph and LLM fallback.

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    if st.session_state.case_id:

        st.markdown("### 📌 Active Case")

        st.markdown(
            f"""
            <div class="glass-card">
                <div style="
                    color:#94a3b8;
                    font-size:0.75rem;
                    text-transform:uppercase;
                ">
                    Company
                </div>
                <div style="
                    color:#f8fafc;
                    font-size:1.1rem;
                    font-weight:750;
                    margin-top:0.3rem;
                ">
                    {st.session_state.company_name}
                </div>
                <div style="
                    color:#a5b4fc;
                    margin-top:0.5rem;
                    font-size:0.85rem;
                ">
                    Case #{st.session_state.case_id}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "🔄 Start New Case",
            use_container_width=True
        ):

            for key, value in defaults.items():

                st.session_state[key] = value

            st.rerun()

    else:

        st.info(
            "Create a case to begin your due-diligence analysis."
        )

    st.markdown("---")

    st.markdown("### 🧠 Workflow")

    workflow_items = [
        ("01", "Create Case"),
        ("02", "Upload Documents"),
        ("03", "Generate Report"),
        ("04", "Review Findings"),
        ("05", "Ask Questions")
    ]

    for number, label in workflow_items:

        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:0.65rem;
                margin:0.55rem 0;
                color:#cbd5e1;
                font-size:0.85rem;
            ">
                <span style="
                    width:27px;
                    height:27px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    border-radius:50%;
                    background:rgba(99,102,241,0.16);
                    color:#a5b4fc;
                    font-size:0.7rem;
                    font-weight:800;
                ">{number}</span>
                </span>{label}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
# ============================================================
# TABS
# ============================================================

tab_case, tab_documents, tab_report, tab_questions = st.tabs(
    [
        "🏢 Case",
        "📄 Documents",
        "📊 Due Diligence Report",
        "💬 Follow-up Questions"
    ]
)
# ============================================================
# CASE TAB
# ============================================================

with tab_case:

    st.markdown(
        '<div class="section-title">'
        '🏢 Create a Due-Diligence Case'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Start an analysis workspace for a company or investment opportunity.'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.case_id:

        st.success(
            f"Active case: #{st.session_state.case_id} — "
            f"{st.session_state.company_name}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        Company
                    </div>
                    <div class="metric-value">
                        {st.session_state.company_name}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        Case ID
                    </div>
                    <div class="metric-value metric-accent">
                        #{st.session_state.case_id}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        Documents
                    </div>
                    <div class="metric-value">
                        {len(st.session_state.documents)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        # LOAD EXISTING CASES
        try:
            cases_response = api_get( "/api/v1/due-diligence" )
            if isinstance(cases_response, list):
                existing_cases = cases_response
            else:
                existing_cases = []
        except Exception as e:
            existing_cases = []
            st.warning( f"Could not load existing cases: {str(e)}" )
        # OPEN EXISTING CASE
        if existing_cases:
            st.markdown("### 📂 Open Existing Case")
            case_options = { ( f"Case #{case['case_id']} — "
                               f"{case['company']} — " 
                               f"{case['due_diligence_type']}" ):
                                 case for case in existing_cases }
            selected_case_label = st.selectbox( "Select a case", list(case_options.keys()), key="existing_case_select" )
            selected_case = case_options[ selected_case_label ]
            if st.button( "📂 Open Selected Case", use_container_width=True ):
                selected_case_id = selected_case["case_id"] 
                try:
                      # ---------------------------------------- 
                      # # Load documents belonging to this case 
                      # # ---------------------------------------- 
                    documents_response = api_get( f"/api/v1/due-diligence/" f"{selected_case_id}/documents" ) 
                    if isinstance( documents_response, list ):
                        st.session_state.documents = ( documents_response )
                    
                    else:
                        st.session_state.documents = []
                          # ---------------------------------------- 
                          # # Set active case 
                          # # ---------------------------------------- 
                    st.session_state.case_id = ( selected_case["case_id"] ) 
                    st.session_state.company_name = ( selected_case["company"] ) 
                    st.session_state.case_type = ( selected_case[ "due_diligence_type" ] ) 
                    st.success( f"Case #{selected_case_id} " "opened successfully." ) 
                    st.rerun() 
                except Exception as e:
                    st.error( f"Could not open case: {str(e)}" )
                    
            else:
                st.info( "No existing cases found. " "Create a new case below." )

            # CREATE NEW CASE
            st.markdown( '<div class="gradient-divider"></div>', unsafe_allow_html=True )
            st.markdown( "### ➕ Create New Case" )


            
            with st.form("create_case_form"):

                company_name = st.text_input(
                    "Company Name",
                    placeholder="e.g. Microsoft Corporation"
                )

                case_type = st.selectbox(
                    "Due Diligence Type",
                    [
                        "Investment",
                        "Acquisition",
                        "Partnership"
                    ]
                )

                submitted = st.form_submit_button(
                    "🚀 Create Due-Diligence Case",
                    use_container_width=True
                )

                if submitted:

                    if not company_name.strip():

                        st.error(
                            "Please enter a company name."
                        )

                    else:

                        try:

                            with st.spinner(
                                "Creating case..."
                            ):

                                result = api_post(
                                    "/api/v1/due-diligence",

                                    json={
                                        "company": company_name.strip(),
                                        "due_diligence_type": case_type
                                }
                                )

                            st.session_state.case_id = (
                                result["case_id"]
                            )

                            st.session_state.company_name = (
                                result["company"]
                            )

                            st.session_state.case_type = case_type
                            st.session_state.documents = []
                            st.success(
                                f"Case #{result['case_id']} "
                                "created successfully!"
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(str(e))


# ============================================================
# DOCUMENT TAB
# ============================================================

with tab_documents:

    st.markdown(
        '<div class="section-title">'
        '📄 Document Intelligence'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Upload annual reports, financial statements, risk documents, '
        'contracts and other due-diligence material.'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.case_id:

        st.warning(
            "Create a case first before uploading documents."
        )

    else:

        st.markdown("### 📤 Upload Document")

        uploaded_file = st.file_uploader(
                "Choose a PDF document",
                type=["pdf"],
                help=(
                    "PDF documents are validated, extracted, "
                    "chunked, embedded and indexed in Qdrant."
                ),
                key="document_uploader"
            )

        document_type = st.selectbox(
                "Document Type",
                [
                    "Annual Report",
                    "Financial Statement",
                    "Investor Presentation",
                    "Risk Report",
                    "Legal Document",
                    "Contract",
                    "Due Diligence Report",
                    "Other"
                ],
                key="document_type_select"
            )

        if document_type == "Other":

            final_document_type = st.text_input(
                "Specify Document Type",
                placeholder="e.g. Regulatory Filing",
                key="custom_document_type"
            )

        else:
            final_document_type = document_type    
        if st.button(
                "⬆️ Upload & Index Document",
                use_container_width=True,
                disabled=uploaded_file is None
            ):

                if not final_document_type.strip():

                    st.error(
                        "Please specify the document type."
                    )

                else:

                    try:

                        with st.spinner(
                            "Processing document..."
                        ):

                            files = {
                                "file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    "application/pdf"
                                )
                            }

                            result = api_post(
                                f"/api/v1/due-diligence/"
                                f"{st.session_state.case_id}/documents",

                                params={
                                    "document_type":
                                        final_document_type
                                },

                                files=files
                            )

                        st.success(
                            result.get(
                                "message",
                                "Document uploaded successfully."
                            )
                        )
                        # RESET DOCUMENT UPLOAD FORM
                        st.session_state.pop( "document_type_select", None )

                        st.session_state.pop( "custom_document_type", None ) 
                        st.session_state.pop( "document_uploader", None ) 
                        st.rerun() 
                    except Exception as e:
                        st.error(str(e))

                        



        # ====================================================
        # LOAD DOCUMENTS
        # ====================================================

        try:

            documents_response = api_get(
                f"/api/v1/due-diligence/"
                f"{st.session_state.case_id}/documents"
            )

            # IMPORTANT:
            # Your main.py returns a LIST directly.
            documents = documents_response

            if isinstance(documents, list):

                st.session_state.documents = documents

        except Exception:

            documents = st.session_state.documents

        st.markdown(
            '<div class="gradient-divider"></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            "### 📚 Uploaded Documents"
        )

        if not st.session_state.documents:

            st.info(
                "No documents uploaded yet."
            )

        else:

            for document in st.session_state.documents:

                filename = document.get(
                    "filename",
                    "Unknown document"
                )

                dtype = document.get(
                    "document_type",
                    "Unknown"
                )

                status = document.get(
                    "status",
                    "unknown"
                )

                if status == "indexed":

                    status_html = (
                        '<span class="status-success">'
                        '✓ READY'
                        '</span>'
                    )

                elif status in [
                    "uploaded",
                    "processing"
                ]:

                    status_html = (
                        '<span class="status-warning">'
                        '● PROCESSING'
                        '</span>'
                    )

                else:

                    status_html = (
                        '<span class="status-danger">'
                        '✕ '
                        + status.upper()
                        + '</span>'
                    )

                st.markdown(
                    f"""
                    <div class="document-card">
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            align-items:center;
                        ">
                            <div>
                                <div class="document-name">
                                    📄 {filename}
                                </div>
                                <div class="document-type">
                                    {dtype}
                                </div>
                            </div>
                            <div>
                                {status_html}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ============================================================
# REPORT TAB
# ============================================================

with tab_report:

    st.markdown(
        '<div class="section-title">'
        '📊 Due-Diligence Report'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Generate a grounded report from indexed evidence using '
        'specialist agents and LangGraph orchestration.'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.case_id:

        st.warning(
            "Create a case first."
        )

    else:
        # ====================================================
        # GENERATE REPORT
        # ====================================================

        if st.button(
            "✨ Generate Due-Diligence Report",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Running multi-agent due-diligence analysis..."
                ):

                    result = api_post(
                        f"/api/v1/due-diligence/"
                        f"{st.session_state.case_id}/generate-report",
                    )

                st.session_state.report = result.get(
                    "report"
                )

                st.session_state.report_type = result.get(
                    "report_type",
                    "full"
                )

                st.session_state.report_sources = result.get(
                    "sources",
                    []
                )

                st.session_state.retrieved_evidence = result.get(
                    "retrieved_evidence",
                    []
                )

                st.session_state.report_metrics = result.get(
                    "synthesis_llm_metrics",
                    {}
                )

                st.success(
                    "Due-diligence report generated successfully."
                )

            except Exception as e:

                st.error(str(e))

        # ====================================================
        # DISPLAY REPORT
        # ====================================================

        report = st.session_state.report

        if report:

            st.markdown(
                '<div class="gradient-divider"></div>',
                unsafe_allow_html=True
            )

            supported = report.get(
                "supported",
                False
            )

            if supported:

                st.markdown(
                    """
                    <span class="status-success">
                    ✓ REPORT GROUNDED IN AVAILABLE EVIDENCE
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    """
                    <span class="status-warning">
                    ⚠ LIMITED EVIDENCE
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)

            
            # =================================================
            # EXECUTIVE SUMMARY
            # =================================================

            executive_summary = report.get(
                "executive_summary"
            )

            if executive_summary:

                st.markdown(
                    f"""
                    <div class="report-section">
                        <div class="report-heading">
                            🧭 Executive Summary
                        </div>
                        <div class="report-text">
                            {executive_summary}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # =================================================
            # COMPANY OVERVIEW
            # =================================================

            company_overview = report.get(
                "company_overview"
            )

            if company_overview:

                st.markdown(
                    f"""
                    <div class="report-section">
                        <div class="report-heading">
                            🏢 Company Overview
                        </div>
                        <div class="report-text">
                            {company_overview}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # =================================================
            # FINANCIAL + RISK
            # =================================================

            financial_analysis = report.get(
                "financial_analysis"
            )

            risk_analysis = report.get(
                "risk_analysis"
            )

            if financial_analysis or risk_analysis:

                col1, col2 = st.columns(2)

                with col1:

                    if financial_analysis:

                        st.markdown(
                            f"""
                            <div class="report-section">
                                <div class="report-heading">
                                    💰 Financial Analysis
                                </div>
                                <div class="report-text">
                                    {financial_analysis}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                with col2:

                    if risk_analysis:

                        st.markdown(
                            f"""
                            <div class="report-section">
                                <div class="report-heading">
                                    ⚠️ Risk Analysis
                                </div>
                                <div class="report-text">
                                    {risk_analysis}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            # =================================================
            # KEY FINDINGS
            # =================================================

            key_findings = report.get(
                "key_findings",
                []
            )

            if key_findings:

                st.markdown(
                    "### 💡 Key Findings"
                )

                for finding in key_findings:

                    st.markdown(
                        f"""
                        <div class="finding">
                            <strong>•</strong> {finding}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # =================================================
            # RED FLAGS
            # =================================================

            red_flags = report.get(
                "red_flags",
                []
            )

            st.markdown(
                "### 🚩 Red Flags"
            )

            if red_flags:

                for flag in red_flags:

                    st.markdown(
                        f"""
                        <div class="red-flag">
                            🚩 {flag}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.success(
                    "No specific red flags were identified "
                    "in the generated report."
                )

            # =================================================
            # LLM METRICS
            # =================================================

            metrics = st.session_state.report_metrics

            if metrics:

                st.markdown(
                    '<div class="gradient-divider"></div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    "### ⚙️ Generation Metrics"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                Model
                            </div>
                            <div style="
                                color:#a5b4fc;
                                font-size:0.95rem;
                                font-weight:700;
                                margin-top:0.5rem;
                            ">
                                {metrics.get(
                                    "model",
                                    "N/A"
                                )}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                Provider
                            </div>
                            <div class="metric-value">
                                {metrics.get(
                                    "provider",
                                    "N/A"
                                )}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col3:

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                Total Tokens
                            </div>
                            <div class="metric-value metric-accent">
                                {metrics.get(
                                    "total_tokens",
                                    "N/A"
                                )}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col4:

                    latency = metrics.get(
                        "latency_seconds",
                        metrics.get(
                            "latency",
                            "N/A"
                        )
                    )

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                Latency
                            </div>
                            <div class="metric-value">
                                {latency}s
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # =================================================
            # EVIDENCE & CITATIONS
            # =================================================

            if (
                st.session_state.report_sources
                or st.session_state.retrieved_evidence):

                st.markdown(
                    '<div class="gradient-divider"></div>',
                    unsafe_allow_html=True
                )

                st.markdown("### 📚 Evidence & Citations")

                st.markdown(
                    """
                    <div class="section-subtitle">
                        Review the exact documents and pages used to support the
                        generated due-diligence analysis.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # -------------------------------------------------
                # Build document lookup
                # -------------------------------------------------

                document_lookup = {
                    str(document.get("document_id")):
                        document.get("filename", "Unknown PDF")
                    for document in st.session_state.documents
                }

                # -------------------------------------------------
                # Prefer retrieved evidence because it contains
                # the actual supporting text.
                # -------------------------------------------------
                if st.session_state.retrieved_evidence:
                    evidence_items = []
                    for evidence_group in st.session_state.retrieved_evidence:
                        if not isinstance(evidence_group,dict):
                            continue

                        chunks = evidence_group.get("chunks",[])

                        if not isinstance(chunks,list):
                            continue
                        agent_name = evidence_group.get("agent")

                        for chunk in chunks:
                            if not isinstance(chunk,dict):
                                continue
                            chunk = chunk.copy()
                            chunk["agent"] = agent_name
                            evidence_items.append(chunk)
                        if evidence_items:

                            for index, evidence in enumerate(evidence_items,start=1):

                                document_id = evidence.get("document_id")

                                filename = document_lookup.get(str(document_id),f"Document #{document_id}")

                                page_number = evidence.get("page_number","N/A")

                                content_type = evidence.get("content_type","text")

                                text = evidence.get("text","")

                                rerank_score = evidence.get("rerank_score")

                                retrieval_score = evidence.get("score")

                        # -----------------------------------------
                        # Evidence card
                        # -----------------------------------------

                            st.markdown(
                                f"""
                                <div class="report-section">
                                    <div class="report-heading">
                                        Evidence
                                    </div>
                                    <div style="
                                        display:flex;
                                        flex-wrap:wrap;
                                        gap:0.55rem;
                                        margin-bottom:0.9rem;
                                    ">
                                        <span style="
                                            background:rgba(99,102,241,0.14);
                                            border:1px solid rgba(129,140,248,0.25);
                                            color:#c4b5fd;
                                            padding:0.3rem 0.65rem;
                                            border-radius:999px;
                                            font-size:0.78rem;
                                            font-weight:700;
                                        ">
                                            📄 {filename}
                                        </span>
                                        <span style="
                                            background:rgba(14,165,233,0.12);
                                            border:1px solid rgba(56,189,248,0.22);
                                            color:#7dd3fc;
                                            padding:0.3rem 0.65rem;
                                            border-radius:999px;
                                            font-size:0.78rem;
                                            font-weight:700;
                                        ">
                                            📑 Page {page_number}
                                        </span>
                                        <span style="
                                            background:rgba(148,163,184,0.10);
                                            border:1px solid rgba(148,163,184,0.18);
                                            color:#cbd5e1;
                                            padding:0.3rem 0.65rem;
                                            border-radius:999px;
                                            font-size:0.78rem;
                                            font-weight:700;
                                        ">
                                            🏷️ {content_type}
                                        </span>
                                    </div>
                                    <div style="
                                        color:#dbeafe;
                                        line-height:1.75;
                                        font-size:0.96rem;
                                        padding:0.9rem 1rem;
                                        background:rgba(15,23,42,0.65);
                                        border-radius:12px;
                                        border-left:3px solid #6366f1;
                                    ">
                                        {text}
                                    </div>
                                    <div style="
                                        margin-top:0.75rem;
                                        color:#64748b;
                                        font-size:0.72rem;
                                    ">
                                        Document ID: {document_id}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # -----------------------------------------
                        # Optional retrieval metadata
                        # -----------------------------------------

                            if (
                                rerank_score is not None
                                or retrieval_score is not None
                            ):

                                metadata_parts = []

                                if retrieval_score is not None:
                                    metadata_parts.append(
                                        f"Semantic score: {float(retrieval_score):.4f}"
                                    )

                                if rerank_score is not None:
                                    metadata_parts.append(
                                        f"Rerank score: {float(rerank_score):.4f}"
                                    )

                                st.caption(
                                    " · ".join(metadata_parts)
                                )

                        else:
                            st.info( "Evidence not available for this report." )
                else:
                    st.info( "Evidence not available for this report." )
                    # -------------------------------------------------
                    # Fallback to report sources if evidence text
                    # is not available.
                    # -------------------------------------------------

                    for index, source in enumerate(
                        st.session_state.report_sources,
                        start=1
                    ):

                        if not isinstance(source, dict):
                            continue

                        document_id = source.get(
                            "document_id"
                        )

                        filename = document_lookup.get(
                            str(document_id),
                            f"Document #{document_id}"
                        )

                        page_number = source.get(
                            "page_number",
                            "N/A"
                        )

                        content_type = source.get(
                            "content_type",
                            "text"
                        )

                        st.markdown(
                            f"""
                            <div class="document-card">
                                <div style="
                                    color:#f8fafc;
                                    font-size:0.95rem;
                                    font-weight:750;
                                    margin-bottom:0.55rem;
                                ">
                                    📄 {filename}
                                </div>
                                <div style="
                                    color:#94a3b8;
                                    font-size:0.82rem;
                                ">
                                    📑 Page {page_number}
                                    &nbsp; · &nbsp;
                                    🏷️ {content_type}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


# ============================================================
# FOLLOW-UP QUESTIONS TAB
# ============================================================

with tab_questions:

    st.markdown(
        '<div class="section-title">'
        '💬 Ask Follow-up Questions'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Ask questions about the indexed evidence after reviewing the report.'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.case_id:

        st.warning(
            "Create a case first."
        )

    else:

        question = st.text_area(
            "Your question",
            placeholder=(
                "Example: What are the major financial risks "
                "mentioned in the documents?"
            ),
            height=120
        )

        if st.button(
            "🧠 Ask AI",
            type="primary",
            use_container_width=True
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                try:

                    with st.spinner(
                        "Searching evidence and generating answer..."
                    ):

                        # Your main.py expects question
                        # as a query parameter.
                        result = api_post(
                            f"/api/v1/due-diligence/"
                            f"{st.session_state.case_id}/ask",

                            params={
                                "question":
                                    question.strip()
                            }
                        )

                    st.session_state.last_question = question

                    st.session_state.last_answer = result.get(
                        "answer",
                        ""
                    )

                    st.session_state.last_sources = result.get(
                        "sources",
                        []
                    )

                except Exception as e:

                    st.error(str(e))

        # ====================================================
        # ANSWER
        # ====================================================

        if st.session_state.last_answer:

            st.markdown(
                '<div class="gradient-divider"></div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div style="
                    color:#94a3b8;
                    font-size:0.8rem;
                    text-transform:uppercase;
                    letter-spacing:0.7px;
                    margin-bottom:0.5rem;
                ">
                    Your Question
                </div>
                <div style="
                    color:#c4b5fd;
                    font-size:1.05rem;
                    font-weight:700;
                    margin-bottom:1rem;
                ">
                    {st.session_state.last_question}
                </div>
                <div class="chat-answer">
                    <div style="
                        color:#a5b4fc;
                        font-weight:750;
                        margin-bottom:0.6rem;
                    ">
                        🤖 AI Analysis
                    </div>
                    {st.session_state.last_answer}
                </div>
                """,
                unsafe_allow_html=True
            )

            # =================================================
            # EVIDENCE & CITATIONS
            # =================================================

            st.markdown(
                '<div class="gradient-divider"></div>',
                unsafe_allow_html=True
            )

            st.markdown(
                "### 📚 Evidence & Citations"
            )

            sources = st.session_state.last_sources

            if sources:

                # Build a lookup for document filenames
                document_lookup = {}

                for document in st.session_state.documents:

                    if isinstance(document, dict):

                        document_id = document.get("id")

                        if document_id is not None:

                            document_lookup[
                                document_id
                            ] = document.get(
                                "filename",
                                f"Document #{document_id}"
                            )

                for index, source in enumerate(
                    sources,
                    start=1
                ):

                    if not isinstance(source, dict):
                        continue

                    # document_id = source.get(
                    #     "document_id"
                    # )

                    document_type = source.get(
                        "document_type",
                        "Unknown"
                    )

                    page_number = source.get(
                        "page_number",
                        "N/A"
                    )

                    # content_type = source.get(
                    #     "content_type",
                    #     "Unknown"
                    # )

                    score = source.get(
                        "score"
                    )
                    rerank_score = source.get( "rerank_score" )
                    evidence_text = source.get( "text", "" )

                    # filename = document_lookup.get(
                    #     document_id,
                    #     f"Document #{document_id}"
                    # )

                    # Format semantic score
                    if isinstance(score, (int, float)):

                        score_display = f"{score:.3f}"

                    else:

                        score_display = "N/A"

                    with st.expander(
                        f"📄 Source {index}"
                    ):

                        st.markdown(
                            f"""
                                <div style="
                                    color:#94a3b8;
                                    font-size:0.82rem;
                                    line-height:1.7;
                                ">
                                    <strong>Document Type:</strong>
                                    {document_type}
                                    &nbsp; | &nbsp;
                                    <strong>Page:</strong>
                                    {page_number}
                                    <br>
                                    <strong>Document ID:</strong>
                                    {document_id}
                                    &nbsp; | &nbsp;
                                    <strong>Semantic Score:</strong>
                                    {score_display}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            "**Evidence used for this answer:**"
                        )
                        if evidence_text:
                             st.markdown( f""" 
                             <div style="
                               background:rgba(15,23,42,0.65);
                                border:1px solid rgba(148,163,184,0.15);
                                border-radius:10px;
                                padding:1rem;
                                margin-top:0.5rem;
                                color:#cbd5e1;
                                font-size:0.9rem;
                                line-height:1.7;
                                ">
                                    {evidence_text}
                                    </div>
                                    """,
                                    unsafe_allow_html=True ) 
                        else:
                            st.info( "Retrieved evidence text is not available " "for this source." )

                        # The current /ask endpoint only returns
                        # source metadata, not the chunk text.
                        # Therefore show the citation metadata here.
            else:

                st.info(
                    "Evidence not available for this question."
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        DueDiligenceAI · AI-powered document intelligence
        <br>
        RAG • Multi-Agent Analysis • Evidence Grounding • LLM Evaluation
    </div>
    """,
    unsafe_allow_html=True
)

# st.title("🔎 DueDiligenceAI")
# st.write(" AI-powered company and investment due diligence platform")

# #Case creation
# st.header("1.Create Due Diligence Case")
# company = st.text_input(
#     "Enter company name",
#     placeholder="e.g. NVIDIA"
# )

# due_diligence_type = st.selectbox(
#     "Due Diligence Type",
#     ["Investment", "Acquisition", "Partnership"]
# )

# if st.button("Create Case"):
#     if not company.strip():

#         st.warning("Please enter a company name.")

#     else:
#         request_data={"company":company,
#                       "due_diligence_type":due_diligence_type}

#         try:

#             response = requests.post(
#                 f"{API_URL}/api/v1/due-diligence",
#                 json=request_data
#             )

#             if response.status_code == 200:

#                 result = response.json()

#                 st.success(
#                     "Due diligence request created!"
#                 )
#                 st.session_state["case_id"] = result["case_id"]
#                 st.session_state["company"] = result["company"]

#                 st.write("Case ID:", result["case_id"])
#                 st.write("Company:", result["company"])
#                 st.write(
#                     "Due Diligence Type:",
#                     result["due_diligence_type"]
#                 )
#                 st.write("Status:", result["status"])


#             else:

#                 st.error(
#                     f"API error: {response.status_code}"
#                 )

#         except requests.exceptions.ConnectionError:

#             st.error(
#                 "Could not connect to the FastAPI backend."
#             )

# #Document upload
# st.divider()
# st.header("2. Upload Due Diligence Documents")

# if "case_id" not in st.session_state:
#     st.info("Create a due diligence case first before uploading documents.")

# else:
#     case_id = st.session_state["case_id"]
#     company = st.session_state["company"]

#     st.write(f"**Company:**{company}")
#     st.write(f"**Case ID:**{case_id}")

#     selected_document_type = st.selectbox(
#         "Document Type",
#         [
#             "Annual Report",
#             "Financial Report",
#             "Investor Presentation",
#             "Risk Report",
#             'Legal Document',
#             "Other"
#         ]
#     )

#     if selected_document_type == "Other":
#         st.warning("Please enter the document type.")
#         document_type = st.text_input("Enter Document Type",placeholder="e.g. ESG Report, Compliance Report")

#     else:
#             document_type = selected_document_type.strip()

#     uploaded_file = st.file_uploader("Upload PDF Document",
#                                      type=["pdf"],
#                                      help="Only PDF documents are supported.")
#     if uploaded_file is not None:
#         st.write(f"Selected file: **{uploaded_file.name}**")

#         if st.button("Upload Document"):
#             if not document_type.strip():
#                 st.warning("Please enter the document type.")
#             else:
#                 files={
#                 "file":(
#                     uploaded_file.name,
#                     uploaded_file.getvalue(),
#                     "application/pdf"
#                 )
#             }

#                 params = {
#                 "document_type":document_type
#             }

#                 try:
#                     response = requests.post(
#                         f"{API_URL}/api/v1/due-diligence/{case_id}/documents",
#                         params=params,
#                         files=files)

#                     if response.status_code == 200:
#                         data=response.json()

#                         st.success("Document uploaded successfully!")
#                         st.write(f"**Document ID:**{data['document_id']}")
#                         st.write(f"**Filename:**{data['filename']}")
#                         st.write(f"**Document Type:**{data['document_type']}")
#                         st.write(f"**Status:**{data['status']}")

#                     else:
#                         st.error(f"Upload failed: {response.text}")

#                 except requests.exceptions.ConnectionError:
#                     st.error("Could not connect to the FastAPI backend."
#                             "Make sure FastAPI is running.")

# #uploaded documents
# st.divider()

# st.header("3.Uploaded Documents")
# if "case_id" not in st.session_state:
#     st.info("Create a due diligence case first.")

# else:
#     case_id = st.session_state["case_id"]

#     try:
#         response=requests.get(f"{API_URL}/api/v1/due-diligence/{case_id}/documents")
#         if response.status_code == 200:
#             documents = response.json()
#             if not documents:
#                 st.info("No documents uploaded for this case yet.")

#             else:
#                 for document in documents:
#                     with st.container(border=True):
#                         st.write(f"**{document['filename']}**")

#                         col1,col2,col3 = st.columns(3)

#                         with col1:
#                             st.write(f"**Type:** {document['document_type']}")
#                         with col2:
#                             st.write(f"**Status:** {document['status']}")
#                         with col3:
#                             st.write(f"**Document ID:** {document['document_id']}")
#         else:
#             st.error(f"Could not retrieve documents;{response.text}")
#     except requests.exceptions.ConnectionError:
#         st.error("Could not connect to the FastAPI backend.")

# st.divider()
# st.header(" Ask Questions about your documents.")
# if "case_id" not in st.session_state:
#     st.info("Create a due diligence case first.")

# else:
#     case_id = st.session_state["case_id"]
#     question = st.text_area(
#         "Enter your question",
#         placeholder="e.g. What happened to the company's revenue in 2025?",
#         height=100
#         )
#     if st.button("Ask Question"):
#         if not question.strip():
#             st.warning("Please enter a question.")

#         else:
#             try:
#                 response = requests.post(
#                     f"{API_URL}/api/v1/due-diligence/{case_id}/ask",
#                     params={
#                         "question": question
#                     }
#                 )
#                 if response.status_code ==200:
#                     result = response.json()
#                     st.subheader("Answer")

#                     st.write(result["answer"])

#                     st.subheader("Sources")

#                     if not result["sources"]:
#                         st.info("No sources were found.")
#                     else:
#                         for source in result["sources"]:
#                             with st.container(border=True):
#                                 st.write(
#                                     "**Document:** "
#                                     f"{source['document_type']}"
#                                 )

#                                 st.write(
#                                     f"**Page:** "
#                                     f"{source['page_number']}"
#                                 )

#                                 st.write(
#                                     f"**Content Type:** "
#                                     f"{source['content_type']}"
#                                 )

#                                 st.write(
#                                     f"**Retrieval Score:** "
#                                     f"{source['score']:.4f}"
#                                 )

#                 else:
#                     st.error(
#                         f"Question answering failed: "
#                         f"{response.text}"
#                     )

#             except requests.exceptions.ConnectionError:

#                 st.error(
#                     "Could not connect to the FastAPI backend. "
#                     "Make sure FastAPI is running."
#                 )
def get_document_filename(document_id):
    """
    Resolve a document_id to the original uploaded PDF filename.
    """
    for document in st.session_state.documents:
        if str(document.get("document_id")) == str(document_id):
            return document.get("filename", "Unknown PDF")

    return f"Document #{document_id}"                            