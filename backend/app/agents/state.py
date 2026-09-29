from typing import TypedDict, List, Dict, Optional,Annotated
from operator import add

class DueDiligenceState(TypedDict, total=False):

    # User input
    question: str
    case_id: int

    due_diligence_type: Optional[str]

    # Routing
    routes: List[str]

    # Agent outputs
    agent_answers: Annotated[List[Dict], add]

    # Retrieved evidence
    retrieved_chunks: List[Dict]
    retrieved_evidence: List[Dict]
    # Final response
    answer: str

    # Sources
    sources: List[Dict]

    # Error information
    error: Optional[str]

    # Report generation
    report_type: Optional[str]
    report: Optional[Dict]

    #guardrails
    guardrail_triggered:bool
    guardrail_reason:Optional[str]

    # LLM observability
    llm_metrics: Annotated[List[Dict], add]
    synthesis_llm_metrics:Dict