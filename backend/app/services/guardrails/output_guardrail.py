import json
from typing import Any, Dict, List

from pydantic import ValidationError
from backend.app.schemas import AgentFinding

ABSTENTION_MESSAGE = ("The information is not available in the provided documents.")

#parse llm output
def parse_llm_output(raw_output: str) ->Dict[str,Any]:
    """convert raw llm response to JSON dictionary."""
    if not raw_output or not raw_output.strip():
        raise ValueError("LLM returned empty response.")

    try:
        parsed_output =json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response is not valid JSON.") from exc

    if not isinstance(parsed_output,dict):
        raise ValueError("LLM response must be a JSON object.")

    return parsed_output

#pydantic structured output validation
def validate_structured_output(
        parsed_output:Dict[str, Any])->AgentFinding:
    """validate the LLM JSON against the AgentFinding schema."""
    try:
        validated_output = AgentFinding.model_validate(parsed_output)
    except ValidationError as exc:
        raise ValueError(f"Invalid structure LLM output: {exc}") from exc
    return validated_output

#evidence validation
def validate_evidence(retrieved_chunks: List[Dict])->Dict[str,Any]:
    """Check whether usable retrieved evidence exists."""
    if not retrieved_chunks:
        return{
            "valid": False,
            "reason":"No retrieved evidence."
        }
    valid_chunks = []
    for chunk in retrieved_chunks:
        if not isinstance(chunk,dict):
            continue
        text = chunk.get("text")
        document_id = chunk.get("document_id")
        page_number = chunk.get("page_number")

        if (
            text
            and str(text).strip()
            and document_id is not None
            and page_number is not None
        ):
            valid_chunks.append(chunk)
    if not valid_chunks:
        return{
            "valid": False,
            "reason":"Retrieved chunks do not contain usable evidence."
        }
    return{
        "valid":True,
        "reason":None,
        "valid_chunks":valid_chunks
    }

#supported flag validation
def validate_supported_flag(
        finding:AgentFinding,
        retrieved_chunks:List[Dict]
    )->Dict[str,Any]:
    """To Make sure the model cannot claim that an answer is supported
    when no usable evidence exists."""

    evidence_result = validate_evidence(retrieved_chunks)
    if finding.supported and not evidence_result["valid"]:
        return{
            "valid":False,
            "reason":(
                "LLM marked the finding as supported, "
                "but no usable evidence exists."
            )
        }
    return{
        "valid":True,
        "reason":None
    }

#source validation
def build_valid_sources(
        retrieved_chunks:List[Dict]
)->List[Dict]:
    """source metadata directly from retrieved chunks."""
    sources= []
    seen = set()

    for chunk in retrieved_chunks:
        document_id = chunk.get("document_id")
        page_number = chunk.get("page_number")

        if(
            document_id is None
            or page_number is None
        ):
            continue
        source_key = (document_id,page_number)

        if source_key in seen:
            continue

        seen.add(source_key)

        sources.append({
            "document_id": document_id,
            "document_type":chunk.get("document_type"),
            "page_number":page_number,
            "content_type": chunk.get("content_type"),
            "score": chunk.get("score"),
            "rerank_score":chunk.get("rerank_score")

        })
    return sources

#complete output guardrail
def validate_agent_output(raw_output:str,
                          retrieved_chunks:List[Dict])->Dict[str,Any]:
     
     """
    Complete output validation pipeline.

    Raw LLM output
        ↓
    JSON parsing
        ↓
    Pydantic validation
        ↓
    Evidence validation
        ↓
    Source validation
        ↓
    Final agent output
    """

     try:

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        parsed_output = parse_llm_output(raw_output)

        # ----------------------------------------------------
        # Validate schema
        # ----------------------------------------------------

        finding = validate_structured_output(parsed_output)

        # ----------------------------------------------------
        # Model explicitly abstained
        # ----------------------------------------------------

        if not finding.supported:

            return {
                "valid": True,
                "finding": ABSTENTION_MESSAGE,
                "supported": False,
                "sources": [],
                "guardrail_triggered": False,
                "reason": "Model abstained."
            }

        # ----------------------------------------------------
        # Validate evidence
        # ----------------------------------------------------

        evidence_result = validate_evidence(retrieved_chunks)

        if not evidence_result["valid"]:

            return {
                "valid": False,
                "finding": ABSTENTION_MESSAGE,
                "supported": False,
                "sources": [],
                "guardrail_triggered": True,
                "reason": evidence_result["reason"]
            }

        # ----------------------------------------------------
        # Validate supported flag
        # ----------------------------------------------------

        supported_result = validate_supported_flag(
            finding,
            retrieved_chunks
        )

        if not supported_result["valid"]:

            return {
                "valid": False,
                "finding": ABSTENTION_MESSAGE,
                "supported": False,
                "sources": [],
                "guardrail_triggered": True,
                "reason": supported_result["reason"]
            }

        # ----------------------------------------------------
        # Build sources
        # ----------------------------------------------------

        sources = build_valid_sources(
            retrieved_chunks
        )

        if not sources:

            return {
                "valid": False,
                "finding": ABSTENTION_MESSAGE,
                "supported": False,
                "sources": [],
                "guardrail_triggered": True,
                "reason": "No valid sources available."
            }

        # ----------------------------------------------------
        # Successful validation
        # ----------------------------------------------------

        return {
            "valid": True,
            "finding": finding.finding.strip(),
            "supported": True,
            "sources": sources,
            "guardrail_triggered": False,
            "reason": None
        }

     except Exception as exc:

        return {
            "valid": False,
            "finding": ABSTENTION_MESSAGE,
            "supported": False,
            "sources": [],
            "guardrail_triggered": True,
            "reason": str(exc)
        }
    