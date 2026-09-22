from typing import TypedDict, List, Dict, Optional,Annotated
from operator import add

class DueDiligenceState(TypedDict, total=False):

    # User input
    question: str
    case_id: int

    # Routing
    routes: List[str]

    # Agent outputs
    agent_answers: Annotated[List[Dict], add]

    # Retrieved evidence
    retrieved_chunks: List[Dict]

    # Final response
    answer: str

    # Sources
    sources: List[Dict]

    # Error information
    error: Optional[str]

    retrieved_evidence: List[Dict]