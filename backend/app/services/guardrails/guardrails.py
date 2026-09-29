from typing import Dict, List, Any
import re

ABSTENTION_MESSAGE = ("The information is not available in the provided documents.")

#1. Prompt injection detection
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?prior\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"override\s+(the\s+)?system\s+prompt",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"show\s+(me\s+)?(your\s+)?system\s+prompt",
    r"reveal\s+your\s+instructions",
    r"show\s+your\s+instructions",
    r"developer\s+message",
    r"system\s+message",
    r"jailbreak",

]

def detect_prompt_injection(text:str)->Dict[str,Any]:
    if not text or not text.strip():
        return{
            "is_suspicious": False,
            "matched_patterns":[]
        }
    normalized_text = text.lower()
    matched_patterns = []

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern,normalized_text):
            matched_patterns.append(pattern)

    return{
        "is_suspicious": len(matched_patterns) >0,
        "matched_patterns": matched_patterns
    }

#2.Evidence guardrail
def validate_evidence(retrieved_evidence:List[Dict],
                      sources:List[Dict])->Dict[str,Any]:
    evidence_chunks=[]
    for agent_result in retrieved_evidence or []:
        chunks = agent_result.get("chunks",[])
        if not isinstance(chunks,list):
            continue

        evidence_chunks.extend(chunks)

    #no evidence
    if not evidence_chunks:
        return{
            "valid":False,
            "reason":"No retrieved evidence was available.",
            "evidence_count":0
        }
    #validate source metadata
    valid_sources = []
    for source in sources or []:
        if not isinstance(source, dict):
            continue

        document_id = source.get("document_id")
        page_number = source.get("page_number")

        if document_id is not None and page_number is not None:
            valid_sources.append(source)

    if not valid_sources:
        return {
            "valid": False,
            "reason": "Retrieved evidence has no valid document sources.",
            "evidence_count": len(evidence_chunks)
        }
    return {
        "valid": True,
        "reason": None,
        "evidence_count": len(evidence_chunks)
    }