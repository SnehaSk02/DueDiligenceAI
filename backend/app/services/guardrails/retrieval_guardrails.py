from typing import Dict, List, Any


# ============================================================
# RETRIEVAL CONFIGURATION
# ============================================================

MAX_RETRIEVAL_K = 20
DEFAULT_RETRIEVAL_K = 10

MIN_RERANK_K = 1
MAX_RERANK_K = 10

# These are initial values.
# Tune them later using your retrieval evaluation dataset.
MIN_RERANK_SCORE = -10.0


# ============================================================
# 1. VALIDATE RETRIEVAL PARAMETERS
# ============================================================

def validate_retrieval_parameters(
    retrieval_k: int,
    rerank_k: int
) -> Dict[str, Any]:
    """
    Prevent unreasonable retrieval sizes.

    This protects both latency and token usage.
    """

    if retrieval_k < 1:
        raise ValueError(
            "retrieval_k must be at least 1."
        )

    if retrieval_k > MAX_RETRIEVAL_K:
        raise ValueError(
            f"retrieval_k cannot exceed {MAX_RETRIEVAL_K}."
        )

    if rerank_k < MIN_RERANK_K:
        raise ValueError(
            "rerank_k must be at least 1."
        )

    if rerank_k > MAX_RERANK_K:
        raise ValueError(
            f"rerank_k cannot exceed {MAX_RERANK_K}."
        )

    if rerank_k > retrieval_k:
        raise ValueError(
            "rerank_k cannot be greater than retrieval_k."
        )

    return {
        "valid": True,
        "retrieval_k": retrieval_k,
        "rerank_k": rerank_k
    }


# ============================================================
# 2. VALIDATE CASE ID
# ============================================================

def validate_case_id(case_id: int) -> int:
    """
    Validate the case identifier before retrieval.
    """

    if case_id is None:
        raise ValueError("case_id is required.")

    if not isinstance(case_id, int):
        raise ValueError("case_id must be an integer.")

    if case_id <= 0:
        raise ValueError("case_id must be greater than zero.")

    return case_id


# ============================================================
# 3. VALIDATE QUERY
# ============================================================

def validate_retrieval_query(
    question: str,
    max_length: int = 2000
) -> str:
    """
    Validate and normalize the retrieval query.
    """

    if not question:
        raise ValueError(
            "Retrieval query cannot be empty."
        )

    question = question.strip()

    if not question:
        raise ValueError(
            "Retrieval query cannot be empty."
        )

    if len(question) > max_length:
        raise ValueError(
            f"Retrieval query cannot exceed {max_length} characters."
        )

    return question


# ============================================================
# 4. VALIDATE RETRIEVED CHUNK
# ============================================================

def validate_retrieved_chunk(
    chunk: Dict
) -> bool:
    """
    Check whether a retrieved chunk contains the metadata
    required by the application.
    """

    if not isinstance(chunk, dict):
        return False

    required_fields = [
        "document_id",
        "page_number",
        "text"
    ]

    for field in required_fields:

        if chunk.get(field) is None:
            return False

    if not str(chunk["text"]).strip():
        return False

    return True


# ============================================================
# 5. CASE ISOLATION
# ============================================================

def validate_case_isolation(
    chunk: Dict,
    case_id: int
) -> bool:
    """
    Make sure a retrieved chunk belongs to the requested case.

    This is an important multi-case security guardrail.
    """

    chunk_case_id = chunk.get("case_id")

    if chunk_case_id is None:
        return False

    try:
        return int(chunk_case_id) == int(case_id)

    except (TypeError, ValueError):
        return False


# ============================================================
# 6. FILTER RETRIEVED RESULTS
# ============================================================

def filter_retrieved_results(
    results: List[Dict],
    case_id: int,
    limit: int
) -> List[Dict]:
    """
    Apply retrieval guardrails to retrieved chunks.

    Checks:
    - valid metadata
    - case isolation
    - non-empty text
    - maximum result count
    """

    validated_results = []

    for result in results:

        if not validate_retrieved_chunk(result):
            continue

        if not validate_case_isolation(
            result,
            case_id
        ):
            continue

        validated_results.append(result)

    return validated_results[:limit]


# ============================================================
# 7. RETRIEVAL QUALITY CHECK
# ============================================================

def validate_retrieval_quality(
    results: List[Dict],
    minimum_results: int = 1
) -> Dict[str, Any]:
    """
    Determine whether retrieval returned usable evidence.

    Note:
    We intentionally do NOT use a hard semantic-score threshold
    here yet because Qdrant scores and cross-encoder scores have
    different meanings. Thresholds should be tuned using the
    existing evaluation dataset.
    """

    if not results:

        return {
            "sufficient": False,
            "reason": "No valid evidence was retrieved.",
            "result_count": 0
        }

    if len(results) < minimum_results:

        return {
            "sufficient": False,
            "reason": (
                "Insufficient retrieval results."
            ),
            "result_count": len(results)
        }

    return {
        "sufficient": True,
        "reason": None,
        "result_count": len(results)
    }


# ============================================================
# 8. COMPLETE RETRIEVAL GUARDRAIL
# ============================================================

def apply_retrieval_guardrails(
    question: str,
    case_id: int,
    results: List[Dict],
    retrieval_k: int,
    rerank_k: int
) -> Dict[str, Any]:
    """
    Run all retrieval guardrails.
    """

    question = validate_retrieval_query(
        question
    )

    case_id = validate_case_id(
        case_id
    )

    validate_retrieval_parameters(
        retrieval_k=retrieval_k,
        rerank_k=rerank_k
    )

    filtered_results = filter_retrieved_results(
        results=results,
        case_id=case_id,
        limit=rerank_k
    )

    quality = validate_retrieval_quality(
        filtered_results
    )

    return {
        "question": question,
        "case_id": case_id,
        "results": filtered_results,
        "sufficient": quality["sufficient"],
        "reason": quality["reason"],
        "result_count": quality["result_count"]
    }