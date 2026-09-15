🔎 DueDiligenceAI
AI-Powered Company & Investment Due Diligence Platform

A production-oriented AI system for analyzing company documents and generating evidence-grounded due diligence insights using RAG, multi-agent workflows, and LLMs.

📌 Overview

DueDiligenceAI is an AI-powered platform designed to assist with company and investment due diligence.

Instead of relying only on a company name, the system is designed around user-provided business documents, such as:

📄 Annual Reports
💰 Financial Reports
📊 Investor Presentations
⚠️ Risk Reports
⚖️ Legal Documents

The platform processes these documents, extracts meaningful information, and will use Retrieval-Augmented Generation (RAG) and specialized AI agents to produce grounded analysis supported by the original source documents.

The project is being developed incrementally with a focus on production-oriented architecture, evaluation, security, latency, and reliable AI outputs.

🏗️ System Architecture
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Streamlit Frontend │
                         └──────────┬──────────┘
                                    │ HTTP
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Backend   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Due Diligence Case│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Document Upload  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │      Document Processing     │
                    │                              │
                    │  PDF Extraction              │
                    │       ↓                      │
                    │  Text Cleaning               │
                    │       ↓                      │
                    │  Table Extraction            │
                    │       ↓                      │
                    │  Document Parsing            │
                    │       ↓                      │
                    │  Structure-Aware Chunking    │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │    Embeddings       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Qdrant Vector Store │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Retrieval       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Reranking       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   LLM / AI Agents   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Evidence-Grounded   │
                         │ Due Diligence Report│
                         └─────────────────────┘