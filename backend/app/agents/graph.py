import json
from langgraph.graph import StateGraph, START, END
from backend.app.services.rag_services import RAGService
from backend.app.agents.state import DueDiligenceState
from backend.app.services.llm_service import LLMService

FINANCIAL_KEYWORDS = [
    "revenue",
    "profit",
    "loss",
    "income",
    "expense",
    "expenses",
    "debt",
    "cash flow",
    "earnings",
    "margin",
    "assets",
    "liabilities",
    "financial performance",
    "financial results",
    "financial statement",
    "financial statements",
    "earnings per share",
    "eps"
]

RISK_KEYWORDS = [
    "risk",
    "risks",
    "threat",
    "threats",
    "uncertainty",
    "uncertainties",
    "regulatory",
    "compliance",
    "legal risk",
    "liability",
    "exposure",
    "foreign currency",
    "foreign exchange",
    "interest rate",
    "credit risk",
    "equity price",
    "liquidity",
    "market risk",
    "cybersecurity",
    "cyber security",
    "competition",
    "competitive risk",
    "supply chain"
]


def keyword_fallback(question: str) -> list[str]:
    """
    Deterministic fallback router used when LLM routing fails.
    """

    question = question.lower()

    has_financial_intent = any(
        keyword in question
        for keyword in FINANCIAL_KEYWORDS
    )

    has_risk_intent = any(
        keyword in question
        for keyword in RISK_KEYWORDS
    )

    routes = []

    if has_financial_intent:
        routes.append("financial")

    if has_risk_intent:
        routes.append("risk")

    if not routes:
        routes.append("general")

    return routes


def llm_route(question: str) -> list[str]:
    """
    Use the LLM to determine which specialized agents
    are relevant to the user's question.
    """

    llm = LLMService()

    prompt = f"""
You are the routing controller for a corporate
due diligence analysis system.

Determine which specialized analysis agents are required
to answer the user's question.

Available agents:

1. financial
   Use for questions involving:
   - revenue
   - profit or loss
   - income
   - expenses
   - margins
   - debt
   - cash flow
   - assets and liabilities
   - financial performance
   - financial statements
   - earnings

2. risk
   Use for questions involving:
   - risks
   - uncertainties
   - exposures
   - regulatory risks
   - legal risks
   - market risks
   - foreign currency risk
   - interest rate risk
   - credit risk
   - liquidity risk
   - cybersecurity risk
   - competition risk
   - supply-chain risk

3. general
   Use when the question does not primarily concern
   financial analysis or risk analysis.

IMPORTANT RULES:

- Select every relevant specialized agent.
- A question can require both financial and risk agents.
- Do not select financial merely because the word
  "financial" appears.
- Select financial when the question actually asks
  about financial information or performance.
- Select risk when the question asks about risks,
  exposures, uncertainties, or risk factors.
- If both topics are present, return both.
- If neither topic is present, return general.
- Return ONLY valid JSON.
- Do not include explanations.

Required JSON format:

{{
    "routes": ["financial"]
}}

or

{{
    "routes": ["risk"]
}}

or

{{
    "routes": ["financial", "risk"]
}}

or

{{
    "routes": ["general"]
}}

USER QUESTION:
{question}
"""

    response = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    result = json.loads(content)

    routes = result.get("routes", [])

    valid_routes = {
        "financial",
        "risk",
        "general"
    }

    routes = [
        route
        for route in routes
        if route in valid_routes
    ]

    if not routes:
        raise ValueError("LLM returned no valid routes.")

    # If specialized routes exist, general is unnecessary.
    if len(routes) > 1 and "general" in routes:
        routes.remove("general")

    return routes


def orchestrator(state: DueDiligenceState) -> DueDiligenceState:
    """
    Production-oriented hybrid orchestrator.

    Primary routing:
        LLM intent classification

    Fallback:
        deterministic keyword routing
    """

    question = state["question"]

    try:
        routes = llm_route(question)

        routing_method = "llm"

    except Exception as e:

        print("\nLLM ROUTING FAILED")
        print("Reason:", str(e))
        print("Using keyword fallback.")

        routes = keyword_fallback(question)

        routing_method = "keyword_fallback"

    print("\n================ ORCHESTRATOR ================")
    print("Question:", question)
    print("Routing method:", routing_method)
    print("Routes:", routes)
    print("================================================")

    return {
        **state,
        "routes": routes
    }


def financial_agent(state: DueDiligenceState) -> DueDiligenceState:
    rag_service = RAGService()

    financial_question = f"""
Extract and analyze ONLY the financial part of the user's question.

Focus exclusively on:
- revenue
- profit or loss
- operating income
- net income
- earnings per share
- expenses
- margins
- debt
- cash flow
- assets and liabilities
- financial performance
- financial trends
- business segment financial performance

IMPORTANT:
If the user's question contains other topics such as risks,
regulatory issues, legal matters, cybersecurity, competition,
or operations, IGNORE those parts.

USER QUESTION:
{state["question"]}

FINANCIAL SUBQUESTION:
"""

    retrieved_chunks = rag_service.retrieve(
    question=f"What was Microsoft's net income in 2025?",
    case_id=state["case_id"],
    top_k=5
)

    if not retrieved_chunks:
        return {
            "agent_answers": [
                {
                    "agent": "financial",
                    "finding": "The information is not available in the provided documents.",
                    "evidence": [],
                    "sources": []
                }
            ]
        }

    context = rag_service.build_context(retrieved_chunks)

    llm = LLMService()

    prompt = f"""
You are the Financial Analysis Agent in a document-based
due diligence system.

Analyze the user's question using ONLY the retrieved
document evidence below.

USER QUESTION:
{state["question"]}

Your task is to answer ONLY the financial aspect of this question.

DOCUMENT EVIDENCE:
{context}

RULES:
1. Focus only on financial information.
2. Do not use outside knowledge.
3. Do not invent facts.
4. Preserve exact numbers, percentages, dates, and financial figures.
5. If the evidence does not contain the requested financial information,
   say:
   "The information is not available in the provided documents."
6. Give a concise factual finding.
7. Do not make investment recommendations.
8. If the question contains multiple topics, answer only the financial topic.
9. Do not create or invent citation markers, source labels, or evidence references.
10. Do not write labels such as "SOURCE 1", "[SOURCE 1]", "【SOURCE 1】",
    "Evidence 1", "[Evidence 1]", or similar.
11. Return only the factual financial finding. The application will display
    document sources separately.

FINANCIAL FINDING:
"""

    response = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    finding = response.choices[0].message.content.strip()

    sources = []

    for chunk in retrieved_chunks:
        sources.append({
            "document_id": chunk["document_id"],
            "document_type": chunk["document_type"],
            "page_number": chunk["page_number"],
            "content_type": chunk["content_type"],
            "score": chunk["score"]
        })

    return {
        "agent_answers": [
            {
                "agent": "financial",
                "finding": finding,
                "evidence": retrieved_chunks,
                "sources": sources
            }
        ]
    }


def risk_agent(state: DueDiligenceState) -> DueDiligenceState:
    rag_service = RAGService()

    risk_question = f"""
Extract and analyze ONLY the risk-related part of the user's question.

Focus exclusively on:
- financial market risks
- foreign currency risk
- interest rate risk
- credit risk
- equity price risk
- liquidity risk
- market risk
- regulatory and legal risks
- operational risks
- cybersecurity risks
- competition risks
- supply chain risks
- business performance risks
- other explicitly disclosed uncertainties

IMPORTANT:
If the user's question contains other topics such as revenue,
profit, expenses, financial performance, or other non-risk topics,
IGNORE those parts.

USER QUESTION:
{state["question"]}

RISK SUBQUESTION:
"""

    retrieved_chunks = rag_service.retrieve(
        question=risk_question,
        case_id=state["case_id"],
        top_k=5
    )

    if not retrieved_chunks:
        return {
            "agent_answers": [
                {
                    "agent": "risk",
                    "finding": "The information is not available in the provided documents.",
                    "evidence": [],
                    "sources": []
                }
            ]
        }

    context = rag_service.build_context(retrieved_chunks)

    llm = LLMService()

    prompt = f"""
You are the Risk Analysis Agent in a document-based
due diligence system.

Analyze the user's question using ONLY the retrieved
document evidence below.

USER QUESTION:
{state["question"]}

Your task is to answer ONLY the risk-related aspect of this question.

DOCUMENT EVIDENCE:
{context}

RULES:
1. Focus only on risks, uncertainties, exposures, and risk factors.
2. Use ONLY information contained in the document evidence.
3. Do not use outside knowledge.
4. Do not invent facts.
5. Do not treat normal financial performance as a risk unless
   the document explicitly identifies it as a risk or uncertainty.
6. Preserve important numbers, percentages, dates, and figures.
7. Identify the specific type of risk when possible.
88. If the evidence does not contain the requested risk information,
   say:
   "The information is not available in the provided documents."
9. Give a concise factual finding.
10. Do not make investment recommendations.
11. If the question contains multiple topics, answer only the risk-related topic.
12. Do not create or invent citation markers, source labels, or evidence references.
13. Do not write labels such as "SOURCE 1", "[SOURCE 1]", "Source 1",
    "【SOURCE 1】", "Evidence 1", "[Evidence 1]", or similar.
14. Return only the factual risk finding. The application will display
    document sources separately.

RISK FINDING:
"""

    response = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    finding = response.choices[0].message.content.strip()

    sources = []

    for chunk in retrieved_chunks:
        sources.append({
            "document_id": chunk["document_id"],
            "document_type": chunk["document_type"],
            "page_number": chunk["page_number"],
            "content_type": chunk["content_type"],
            "score": chunk["score"]
        })

    return {
        "agent_answers": [
            {
                "agent": "risk",
                "finding": finding,
                "evidence": retrieved_chunks,
                "sources": sources
            }
        ]
    }


def general_agent(state: DueDiligenceState) -> DueDiligenceState:

    rag_service = RAGService()

    general_question = f"""
Analyze the following user question from a general
due diligence perspective.

Retrieve information relevant to the question from the
provided company documents.

USER QUESTION:
{state["question"]}
"""

    retrieved_chunks = rag_service.retrieve(
        question=general_question,
        case_id=state["case_id"],
        top_k=5
    )

    if not retrieved_chunks:
        return {
            "agent_answers": [
                {
                    "agent": "general",
                    "finding": "The information is not available in the provided documents.",
                    "evidence": [],
                    "sources": []
                }
            ]
        }

    context = rag_service.build_context(retrieved_chunks)

    llm = LLMService()

    prompt = f"""
You are the General Due Diligence Agent in a
document-based due diligence system.

Analyze the user's question using ONLY the retrieved
document evidence below.

USER QUESTION:
{state["question"]}

DOCUMENT EVIDENCE:
{context}

RULES:

1. Answer the user's question using ONLY the document evidence.
2. Do not use outside knowledge.
3. Do not invent or assume facts.
4. Preserve important numbers, dates, percentages,
   and other relevant figures.
5. If the evidence does not contain the requested information,
   say:

   "The information is not available in the provided documents."

6. Give a concise factual finding.
7. Do not make investment recommendations.
8. Do not create or invent citation markers such as
   [Evidence 1], 【Evidence 1】, or SOURCE 1.

GENERAL FINDING:
"""

    response = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    finding = response.choices[0].message.content.strip()

    sources = []

    for chunk in retrieved_chunks:
        sources.append({
            "document_id": chunk["document_id"],
            "document_type": chunk["document_type"],
            "page_number": chunk["page_number"],
            "content_type": chunk["content_type"],
            "score": chunk["score"]
        })

    return {
        "agent_answers": [
            {
                "agent": "general",
                "finding": finding,
                "evidence": retrieved_chunks,
                "sources": sources
            }
        ]
    }


def synthesis_agent(state: DueDiligenceState) -> DueDiligenceState:
    print("\n================ SYNTHESIS INPUT ================")

    agent_answers = state.get("agent_answers", [])

    print("Number of agent results:", len(agent_answers))

    for result in agent_answers:
        print("\nAgent:", result.get("agent"))
        print("Finding:", result.get("finding"))
        print(
            "Number of evidence chunks:",
            len(result.get("evidence", []))
        )
        print("Sources:", result.get("sources"))

    print("==================================================\n")

    if not agent_answers:
        return {
            **state,
            "answer": "No agent results were available.",
            "sources": []
        }

    context_parts = []

    for result in agent_answers:

        evidence_text = []

        for i, chunk in enumerate(
            result.get("evidence", []),
            start=1
        ):
            evidence_text.append(
                f"""
Evidence {i}
Document: {chunk.get("document_type")}
Page: {chunk.get("page_number")}
Content type: {chunk.get("content_type")}

{chunk.get("text")}
"""
            )

        context_parts.append(
            f"""
AGENT: {result.get("agent")}

AGENT FINDING:
{result.get("finding")}

RETRIEVED DOCUMENT EVIDENCE:
{"".join(evidence_text)}
"""
        )

    agent_context = "\n".join(context_parts)

    prompt = f"""
You are the final synthesis agent in a document-based
due diligence system.

The specialized agents analyzed the user's question
using retrieved evidence from the company's documents.

Your task is to produce ONE final answer using ONLY
the retrieved document evidence.

USER QUESTION:
{state["question"]}

SPECIALIZED AGENT ANALYSIS:
{agent_context}

RULES:

1. Use ONLY the retrieved document evidence provided above.

2. Do not use outside knowledge.

3. Do not invent or assume facts.

4. Treat the retrieved document evidence as the
   authoritative source.

5. Agent findings are interpretations of the evidence.
   Verify them against the actual retrieved evidence.

6. Preserve important numbers, dates, percentages,
   financial figures, and risk categories.

7. If multiple agents provide relevant information,
   combine the relevant findings into one coherent answer.

8. Do not include information that is unsupported by
   the retrieved evidence.

9. If the retrieved evidence does not contain enough
   information to answer the question, say:

   "The information is not available in the provided documents."

10. Do not make investment recommendations.

11. Give a concise, factual answer.

12. Do not create, invent, or output evidence labels such as
    "Evidence 1", "Evidence 2", "SOURCE 1", "[Evidence 1]",
    or similar citation markers.

13. Do not create citations or references that are not explicitly
    provided in the input.

FINAL ANSWER:

Return only the factual answer to the user's question.
Do not include source numbers, evidence labels, citation markers,
or references such as [Evidence 1], 【Evidence 1】, or SOURCE 1.
The application will display the document sources separately.
"""

    llm = LLMService()

    response = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    final_answer = response.choices[0].message.content.strip()

    all_sources = []

    for result in agent_answers:
        all_sources.extend(
            result.get("sources", [])
        )

    unique_sources = []
    seen_sources = set()

    for source in all_sources:

        source_key = (
            source.get("document_id"),
            source.get("page_number")
        )

        if source_key not in seen_sources:
            seen_sources.add(source_key)
            unique_sources.append(source)

    retrieved_evidence = [
    {
        "agent": result.get("agent"),
        "chunks": result.get("evidence", [])
    }
    for result in agent_answers
]
    print("\nDEBUG retrieved_evidence:")
    print(retrieved_evidence)

    return {
        **state,
        "answer": final_answer,
        "sources": unique_sources,
        "retrieved_evidence": retrieved_evidence
    }

def route_question(state: DueDiligenceState) -> list[str]:
    """
    Route the workflow to the appropriate agent.
    """

    return state["routes"]


# Create graph
builder = StateGraph(DueDiligenceState)

# Add nodes
builder.add_node("orchestrator", orchestrator)
builder.add_node("financial", financial_agent)
builder.add_node("risk", risk_agent)
builder.add_node("general", general_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "orchestrator")


# Conditional routing
builder.add_conditional_edges(
    "orchestrator",
    route_question,
    {
        "financial": "financial",
        "risk": "risk",
        "general": "general"
    }
)

# End points
builder.add_edge("financial", "synthesis")
builder.add_edge("risk", "synthesis")
builder.add_edge("general", "synthesis")

builder.add_edge("synthesis", END)


# Compile graph
due_diligence_graph = builder.compile()