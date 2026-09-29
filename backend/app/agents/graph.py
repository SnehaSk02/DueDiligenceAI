import json
from langgraph.graph import StateGraph, START, END
from backend.app.services.rag_services import RAGService
from backend.app.agents.state import DueDiligenceState
from backend.app.services.llm_gateway import gateway
from backend.app.services.guardrails.output_guardrail import validate_agent_output
from backend.app.services.guardrails.generation_guardrails import generation_guardrails


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

    response = gateway.generate(
    prompt=prompt,
    temperature=0,
    response_format={"type": "json_object"}
)

    content = response["content"].strip()

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

    #report generation
    report_type = state.get("report_type")
    print("\nDEBUG ORCHESTRATOR STATE:")
    print(state)
    print("DEBUG REPORT TYPE:", state.get("report_type"))

    if report_type:
        if report_type == "full":
            routes=["financial","risk","general"]
        elif report_type == "financial":
            routes=["financial"]
        elif report_type == "risk":
            routes = ["risk"]
        else:
            raise ValueError(f"Unsupported report type:{report_type}")

        print("\n================ ORCHESTRATOR ================")
        print("MODE: REPORT")
        print("Report type:", report_type)
        print("Routes:", routes)
        print("================================================")

        return {
            "routes": routes
        }

    #NormalQ&A
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

    due_diligence_type = state.get(
    "due_diligence_type",
    "Investment")
    report_mode = bool(state.get("report_type"))
    
    if report_mode:

        financial_question = """
Analyze the company's financial position for a due diligence report.

Focus exclusively on information explicitly available in the
provided company documents.

Analyze, where supported by the documents:

- Revenue
- Revenue growth
- Profit and loss
- Operating income
- Net income
- Earnings per share
- Expenses
- Profit margins
- Assets
- Liabilities
- Debt
- Cash flow
- Liquidity
- Financial performance
- Financial trends
- Business segment financial performance

Do not infer missing information.

If a financial metric or topic is not available in the documents,
do not invent it.
"""

    else:

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
    if report_mode:
        retrieval_query = """
            Analyze the company's financial position for due diligence.

            Retrieve information about:

            - Revenue
            - Revenue growth
            - Profit and loss
            - Operating income
            - Net income
            - Earnings per share
            - Expenses
            - Profit margins
            - Assets
            - Liabilities
            - Debt
            - Cash flow
            - Liquidity
            - Financial performance
            - Financial trends
            - Business segment financial performance

            Focus only on information explicitly available in the
            provided company documents.
            """
    else:
        retrieval_query = state["question"]

    retrieved_chunks = rag_service.retrieve(
        question=retrieval_query,
        case_id=state["case_id"],
        top_k=5
    )

    if not retrieved_chunks:
        return {
                "agent_answers": [
                    {
                        "agent": "financial",
                        "finding": "The information is not available in the provided documents.",
                        "supported": False,
                        "evidence": [],
                        "sources": [],
                        "guardrail_triggered": True,
                        "guardrail_reason": "No retrieved evidence."

                    }
                ]
            }

    context = rag_service.build_context(retrieved_chunks)

    if report_mode:

        prompt = f"""
    You are the Financial Analysis Agent in a document-based
    corporate due diligence system.
    The business purpose of this due diligence is:
    {due_diligence_type}
    The user requested a {state["report_type"]} due diligence report.

    Analyze the company's financial information using ONLY the
    retrieved document evidence below.

    DOCUMENT EVIDENCE:
    {context}

    {generation_guardrails}

    RULES:

    1. Analyze only financial information.
    2. Do not use outside knowledge.
    3. Do not invent facts.
    4. Preserve exact numbers, percentages, dates, and financial figures.
    5. Identify important financial trends when directly supported.
    6. If information is unavailable, explicitly state that it is
    not available in the provided documents.
    7. Do not make investment recommendations.
    8. Do not create citation markers.
    9. Do not create source labels.
    10. Return ONLY a JSON object.
    11. The JSON must contain exactly:
        "finding"
        "supported"
    12. "supported" must be a boolean.
    13. Do not include markdown.

    JSON FORMAT:

    {{
        "finding": "Factual financial analysis based only on the evidence.",
        "supported": true
    }}
    """

    else:

        prompt = f"""
    You are the Financial Analysis Agent in a document-based
    due diligence system.

    Analyze the user's question using ONLY the retrieved
    document evidence below.

    USER QUESTION:
    {state["question"]}

    DOCUMENT EVIDENCE:
    {context}

    {generation_guardrails}

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
    8. Do not create citation markers.
    9. Return ONLY a JSON object with exactly:
    "finding" and "supported".
    10. "supported" must be a boolean.
    11. Do not include markdown or code fences.

    JSON FORMAT:

    {{
        "finding": "Your factual financial finding.",
        "supported": true
    }}
    """

    response = gateway.generate(
            prompt=prompt,
            temperature=0,
            response_format = {"type":"json_object"}
        )

    raw_output = response["content"].strip()
    validation_result = validate_agent_output(raw_output=raw_output,
                                                retrieved_chunks=retrieved_chunks)
    finding = validation_result["finding"]
    supported = validation_result["supported"]
    sources = validation_result["sources"]  
    print("\nDEBUG: LLM RESPONSE RECEIVED")
    print("Raw output:", raw_output)

    print("\nDEBUG: VALIDATION RESULT")
    print(validation_result)

    print("\nDEBUG: FINANCIAL AGENT RETURNING RESULT")
    
    print("\nDEBUG: FINANCIAL AGENT EXECUTED")
    return {
            "agent_answers": [
                {
                    "agent": "financial",
                    "finding": finding,
                    "supported": supported,
                    "evidence": retrieved_chunks,
                    "sources": sources,
                    "guardrail_triggered": validation_result["guardrail_triggered"],
                    "guardrail_reason": validation_result["reason"]}],
                    "llm_metrics":[ {
                        "agent": "financial",
                        "model": response.get("model"),
                    "provider": response.get("provider"),
                    "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                    "latency_seconds": response.get("latency_seconds", 0),
                    "attempts": response.get("attempts", 0)
                    
                    }
                    ]
                    }
                
            


def risk_agent(state: DueDiligenceState) -> DueDiligenceState:
    rag_service = RAGService()
    due_diligence_type = state.get(
    "due_diligence_type",
    "Investment")
    report_mode = bool(state.get("report_type"))

    if report_mode:

        risk_question =f"""
Analyze the company's risk profile for a due diligence report.
The business purpose of this due diligence is:
{due_diligence_type}
Focus exclusively on information explicitly available in the
provided company documents.

Retrieve information related to:

- Business risks
- Market risks
- Competitive risks
- Regulatory risks
- Legal risks
- Compliance risks
- Financial risks
- Liquidity risks
- Credit risks
- Interest rate risks
- Foreign exchange risks
- Cybersecurity risks
- Operational risks
- Supply chain risks
- Technology risks
- Strategic risks
- Concentration risks
- Material uncertainties
- Contingent liabilities
- Other explicitly disclosed risks

Do not infer missing risks.

If a risk or risk-related topic is not available in the documents,
do not invent it.
"""

        retrieval_query = risk_question

    else:

        risk_question = f"""
Extract and analyze ONLY the risk-related part of the user's question.

Focus exclusively on:

- business risks
- market risks
- competitive risks
- regulatory risks
- legal risks
- compliance risks
- financial risks
- liquidity risks
- credit risks
- interest rate risks
- foreign exchange risks
- cybersecurity risks
- operational risks
- supply chain risks
- technology risks
- strategic risks

IMPORTANT:
If the user's question contains financial metrics,
revenue, profit, expenses, or other non-risk topics,
IGNORE those parts.

USER QUESTION:
{state["question"]}

RISK SUBQUESTION:
"""

        retrieval_query = state["question"]

    retrieved_chunks = rag_service.retrieve(
        question=retrieval_query,
        case_id=state["case_id"],
        top_k=5
    )

    if not retrieved_chunks:
        return {
                    "agent_answers": [
                        {
                            "agent": "risk",
                            "finding": "The information is not available in the provided documents.",
                            "supported": False,
                            "evidence": [],
                            "sources": [],
                            "guardrail_triggered": True,
                            "guardrail_reason": "No retrieved evidence."
        
                        }
                    ]
                }

    context = rag_service.build_context(retrieved_chunks)

    if report_mode:

        prompt = f"""
    You are the Risk Analysis Agent in a document-based
    corporate due diligence system.

    The user requested a {state["report_type"]} due diligence report.

    Analyze the company's risk information using ONLY the
    retrieved document evidence below.

    DOCUMENT EVIDENCE:
    {context}

    {generation_guardrails}

    RULES:

    1. Analyze only risk-related information.
    2. Do not use outside knowledge.
    3. Do not invent risks.
    4. Preserve exact facts, dates, percentages, amounts,
    and other relevant details from the evidence.
    5. Identify important risk factors and trends when directly
    supported by the documents.
    6. If risk information is unavailable, explicitly state that it
    is not available in the provided documents.
    7. Do not make investment recommendations.
    8. Do not create citation markers.
    9. Do not create source labels.
    10. Return ONLY a JSON object.
    11. The JSON must contain exactly:
        "finding"
        "supported"
    12. "supported" must be a boolean.
    13. Do not include markdown.

    JSON FORMAT:

    {{
        "finding": "Factual risk analysis based only on the evidence.",
        "supported": true
    }}
    """

    else:

        prompt = f"""
    You are the Risk Analysis Agent in a document-based
    due diligence system.

    Analyze the user's question using ONLY the retrieved
    document evidence below.

    USER QUESTION:
    {state["question"]}

    DOCUMENT EVIDENCE:
    {context}

    {generation_guardrails}

    RULES:

    1. Focus only on risk-related information.
    2. Do not use outside knowledge.
    3. Do not invent facts or risks.
    4. Preserve exact facts, dates, percentages, and amounts.
    5. If the evidence does not contain the requested risk information,
    say:
    "The information is not available in the provided documents."
    6. Give a concise factual finding.
    7. Do not make investment recommendations.
    8. Do not create citation markers.
    9. Return ONLY a JSON object with exactly:
    "finding" and "supported".
    10. "supported" must be a boolean.
    11. Do not include markdown or code fences.

    JSON FORMAT:

    {{
        "finding": "Your factual risk finding.",
        "supported": true
    }}
    """

    response = gateway.generate(
        prompt=prompt,
        temperature=0,
        response_format = {"type":"json_object"}
            )
        
    raw_output = response["content"].strip()
    validation_result = validate_agent_output(raw_output=raw_output,
                                                    retrieved_chunks=retrieved_chunks)
    finding = validation_result["finding"]
    supported = validation_result["supported"]
    sources = validation_result["sources"]  
            
        
    return {
            "agent_answers": [
                    {
                        "agent": "risk",
                        "finding": finding,
                        "supported": supported,
                        "evidence": retrieved_chunks,
                        "sources": sources,
                        "guardrail_triggered": validation_result["guardrail_triggered"],
                        "guardrail_reason": validation_result["reason"]}],
                                        "llm_metrics":[ {
                                            "agent": "risk",
                                            "model": response.get("model"),
                                        "provider": response.get("provider"),
                                        "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                                        "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                                        "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                                        "latency_seconds": response.get("latency_seconds", 0),
                                        "attempts": response.get("attempts", 0)
                                        
                                        }
                                        ]
                                        }
    

    

def general_agent(state: DueDiligenceState) -> DueDiligenceState:

    rag_service = RAGService()
    due_diligence_type = state.get(
    "due_diligence_type",
    "Investment")
    report_mode = bool(state.get("report_type"))

    if report_mode:

        general_question = f"""
Analyze the company from a general due diligence perspective.
The business purpose of this due diligence is:
{due_diligence_type}
Focus exclusively on information explicitly available in the
provided company documents.

Retrieve information related to:

- Company overview
- Business model
- Products and services
- Business segments
- Geographic presence
- Major markets
- Customers and customer concentration
- Suppliers and dependencies
- Strategic initiatives
- Business operations
- Competitive position
- Corporate developments
- Material events
- Other important company-level information relevant to
  due diligence

Do not infer missing information.

If information is not available in the documents,
do not invent it.
"""

        retrieval_query = general_question

    else:

        general_question = f"""
Analyze the following user question from a general
due diligence perspective.

Focus on company-level information such as:

- company overview
- business model
- products and services
- business segments
- geographic presence
- customers
- suppliers
- operations
- strategy
- competitive position
- corporate developments

Do not focus primarily on detailed financial metrics or
specific risk analysis unless they are directly relevant
to answering the user's question.

USER QUESTION:
{state["question"]}

GENERAL DUE DILIGENCE SUBQUESTION:
"""

        retrieval_query = state["question"]

    retrieved_chunks = rag_service.retrieve(
        question=retrieval_query,
        case_id=state["case_id"],
        top_k=5
    )

    if not retrieved_chunks:
        return {
            "agent_answers": [
                {
                    "agent": "general",
                    "finding": "The information is not available in the provided documents.",
                    "supported": False,
                    "evidence": [],
                    "sources": [],
                    "guardrail_triggered": True,
                    "guardrail_reason": "No retrieved evidence."
                }
            ]
        }

    context = rag_service.build_context(retrieved_chunks)

    if report_mode:

        prompt = f"""
You are the General Due Diligence Agent in a document-based
corporate due diligence system.

The user requested a {state["report_type"]} due diligence report.

Analyze the company's general business information using ONLY
the retrieved document evidence below.

DOCUMENT EVIDENCE:
{context}

{generation_guardrails}

RULES:

1. Analyze only general company and business information.
2. Do not use outside knowledge.
3. Do not invent facts.
4. Preserve exact facts, dates, names, figures, and other
   relevant details from the evidence.
5. Identify important company-level findings when directly
   supported by the documents.
6. If information is unavailable, explicitly state that it
   is not available in the provided documents.
7. Do not make investment recommendations.
8. Do not create citation markers.
9. Do not create source labels.
10. Return ONLY a JSON object.
11. The JSON must contain exactly:
    "finding"
    "supported"
12. "supported" must be a boolean.
13. Do not include markdown.

JSON FORMAT:

{{
    "finding": "Factual general due diligence analysis based only on the evidence.",
    "supported": true
}}
"""

    else:

        prompt = f"""
You are the General Due Diligence Agent in a document-based
due diligence system.

Analyze the user's question using ONLY the retrieved
document evidence below.

USER QUESTION:
{state["question"]}

DOCUMENT EVIDENCE:
{context}

{generation_guardrails}

RULES:

1. Focus on general company and business information.
2. Do not use outside knowledge.
3. Do not invent facts.
4. Preserve exact facts, dates, names, and figures.
5. If the evidence does not contain the requested information,
   say:
   "The information is not available in the provided documents."
6. Give a concise factual finding.
7. Do not make investment recommendations.
8. Do not create citation markers.
9. Return ONLY a JSON object with exactly:
   "finding" and "supported".
10. "supported" must be a boolean.
11. Do not include markdown or code fences.

JSON FORMAT:

{{
    "finding": "Your factual general due diligence finding.",
    "supported": true
}}
"""

    response = gateway.generate(
        prompt=prompt,
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_output = response["content"].strip()

    validation_result = validate_agent_output(
        raw_output=raw_output,
        retrieved_chunks=retrieved_chunks
    )

    finding = validation_result["finding"]
    supported = validation_result["supported"]
    sources = validation_result["sources"]

    return {
        "agent_answers": [
            {
                "agent": "general",
                "finding": finding,
                "supported": supported,
                "evidence": retrieved_chunks,
                "sources": sources,
                "guardrail_triggered": validation_result["guardrail_triggered"],
                "guardrail_reason": validation_result["reason"]
            }
        ],
        "llm_metrics": [
            {
                "agent": "general",
                "model": response.get("model"),
                "provider": response.get("provider"),
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                "latency_seconds": response.get("latency_seconds", 0),
                "attempts": response.get("attempts", 0)
            }
        ]
    }


def synthesis_agent(state: DueDiligenceState) -> DueDiligenceState:
    print("\n================ SYNTHESIS INPUT ================")

    agent_answers = state.get("agent_answers", [])
    due_diligence_type = state.get(
        "due_diligence_type",
        "Investment")
    report_type = state.get("report_type")

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
            "sources": [],
            "retrieved_evidence": []
        }

    if report_type:

        context_parts = []

        for result in agent_answers:

            evidence_text = []

            for i, chunk in enumerate(
                result.get("evidence", []),
                start=1
            ):
                evidence_text.append(
                    f"""
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

DOCUMENT EVIDENCE:
{"".join(evidence_text)}
"""
            )

        agent_context = "\n".join(context_parts)

        prompt = f"""
You are the final synthesis agent in a document-based
corporate due diligence system.
BUSINESS PURPOSE:
{due_diligence_type}
The user requested a:

{report_type}
The business purpose tells you why the due diligence
is being performed.

Your task is to create a structured due diligence report
using ONLY the findings and document evidence provided
by the specialist agents.

SPECIALIST AGENT ANALYSIS:

{agent_context}

{generation_guardrails}

IMPORTANT RULES:

1. Use ONLY information supported by the retrieved document evidence.

2. Do not use outside knowledge.

3. Do not invent facts, numbers, dates, risks, or company information.

4. Agent findings are interpretations. Verify them against the
   retrieved evidence before including them.

5. Preserve exact numbers, percentages, dates, and financial figures.

6. If information required for a section is not available,
   clearly state:
   "The information is not available in the provided documents."

7. Do not make investment recommendations.

8. Do not create unsupported conclusions.

9. Potential red flags must be based on explicitly disclosed
   evidence from the documents.

10. Do not create citation markers such as:
    SOURCE 1
    Evidence 1
    [SOURCE 1]

11. Return ONLY valid JSON.

12. Do not include markdown or code fences.

REPORT STRUCTURE:

{{
    "executive_summary": "Concise summary of the major findings.",

    "company_overview": "Overview of the company and its business based on the documents.",

    "financial_analysis": "Financial findings supported by the documents.",

    "risk_analysis": "Risk findings supported by the documents.",

    "key_findings": [
        "Important finding 1",
        "Important finding 2"
    ],

    "red_flags": [
        "Potential concern explicitly supported by the documents"
    ],

    "supported": true
}}

REPORT TYPE:
{report_type}
"""

        response = gateway.generate(
            prompt=prompt,
            temperature=0,
            response_format={"type": "json_object"}
        )

        raw_output = response["content"].strip()

        try:

            report = json.loads(raw_output)

        except json.JSONDecodeError:

            return {
                "answer": raw_output,
                "report": None,
                "sources": [],
                "retrieved_evidence": [],
                "guardrail_triggered": True,
                "guardrail_reason": "Report JSON parsing failed."
            }

        # -----------------------------------------------------
        # Collect sources
        # -----------------------------------------------------

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

        return {
            "report": report,

            # Useful for frontend compatibility
            "answer": report.get(
                "executive_summary",
                ""
            ),

            "sources": unique_sources,

            "retrieved_evidence": retrieved_evidence,

            "guardrail_triggered": False,

            "guardrail_reason": None,

            "synthesis_llm_metrics": {
                "model": response["model"],
                "provider": response["provider"],
                "prompt_tokens": response["usage"]["prompt_tokens"],
                "completion_tokens": response["usage"]["completion_tokens"],
                "total_tokens": response["usage"]["total_tokens"],
                "latency_seconds": response["latency_seconds"],
                "attempts": response["attempts"]
            }
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