import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="DueDiligenceAI",page_icon="🔎", layout="wide")

st.title("🔎 DueDiligenceAI")
st.write(" AI-powered company and investment due diligence platform")

#Case creation
st.header("1.Create Due Diligence Case")
company = st.text_input(
    "Enter company name",
    placeholder="e.g. NVIDIA"
)

due_diligence_type = st.selectbox(
    "Due Diligence Type",
    ["Investment", "Acquisition", "Partnership"]
)

if st.button("Create Case"):
    if not company.strip():

        st.warning("Please enter a company name.")

    else:
        request_data={"company":company,
                      "due_diligence_type":due_diligence_type}

        try:

            response = requests.post(
                f"{API_URL}/api/v1/due-diligence",
                json=request_data
            )

            if response.status_code == 200:

                result = response.json()

                st.success(
                    "Due diligence request created!"
                )
                st.session_state["case_id"] = result["case_id"]
                st.session_state["company"] = result["company"]

                st.write("Case ID:", result["case_id"])
                st.write("Company:", result["company"])
                st.write(
                    "Due Diligence Type:",
                    result["due_diligence_type"]
                )
                st.write("Status:", result["status"])


            else:

                st.error(
                    f"API error: {response.status_code}"
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the FastAPI backend."
            )

#Document upload
st.divider()
st.header("2. Upload Due Diligence Documents")

if "case_id" not in st.session_state:
    st.info("Create a due diligence case first before uploading documents.")

else:
    case_id = st.session_state["case_id"]
    company = st.session_state["company"]

    st.write(f"**Company:**{company}")
    st.write(f"**Case ID:**{case_id}")

    selected_document_type = st.selectbox(
        "Document Type",
        [
            "Annual Report",
            "Financial Report",
            "Investor Presentation",
            "Risk Report",
            'Legal Document',
            "Other"
        ]
    )

    if selected_document_type == "Other":
        st.warning("Please enter the document type.")
        document_type = st.text_input("Enter Document Type",placeholder="e.g. ESG Report, Compliance Report")

    else:
            document_type = selected_document_type.strip()

    uploaded_file = st.file_uploader("Upload PDF Document",
                                     type=["pdf"],
                                     help="Only PDF documents are supported.")
    if uploaded_file is not None:
        st.write(f"Selected file: **{uploaded_file.name}**")

        if st.button("Upload Document"):
            if not document_type.strip():
                st.warning("Please enter the document type.")
            else:
                files={
                "file":(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            }

                params = {
                "document_type":document_type
            }

                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/due-diligence/{case_id}/documents",
                        params=params,
                        files=files)

                    if response.status_code == 200:
                        data=response.json()

                        st.success("Document uploaded successfully!")
                        st.write(f"**Document ID:**{data['document_id']}")
                        st.write(f"**Filename:**{data['filename']}")
                        st.write(f"**Document Type:**{data['document_type']}")
                        st.write(f"**Status:**{data['status']}")

                    else:
                        st.error(f"Upload failed: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the FastAPI backend."
                            "Make sure FastAPI is running.")

#uploaded documents
st.divider()

st.header("3.Uploaded Documents")
if "case_id" not in st.session_state:
    st.info("Create a due diligence case first.")

else:
    case_id = st.session_state["case_id"]

    try:
        response=requests.get(f"{API_URL}/api/v1/due-diligence/{case_id}/documents")
        if response.status_code == 200:
            documents = response.json()
            if not documents:
                st.info("No documents uploaded for this case yet.")

            else:
                for document in documents:
                    with st.container(border=True):
                        st.write(f"**{document['filename']}**")

                        col1,col2,col3 = st.columns(3)

                        with col1:
                            st.write(f"**Type:** {document['document_type']}")
                        with col2:
                            st.write(f"**Status:** {document['status']}")
                        with col3:
                            st.write(f"**Document ID:** {document['document_id']}")
        else:
            st.error(f"Could not retrieve documents;{response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the FastAPI backend.")