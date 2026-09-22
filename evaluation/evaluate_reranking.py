import json
from pathlib import Path

from backend.app.services.rag_services import RAGService
from backend.app.services.reranker import reranker


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = PROJECT_ROOT / "evaluation" / "dataset.json"
OUTPUT_PATH = PROJECT_ROOT / "evaluation" / "reranking_results.json"


# ============================================================
# CONFIGURATION
# ============================================================

RETRIEVAL_K = 10
RERANK_K = 5


# ============================================================
# LOAD DATASET
# ============================================================

with open(
    DATASET_PATH,
    "r",
    encoding="utf-8"
) as file:

    dataset = json.load(file)


# ============================================================
# SERVICES
# ============================================================

rag_service = RAGService()


# ============================================================
# GROUND TRUTH HELPERS
# ============================================================

def build_ground_truth(item):
    """
    Ground truth is based on:

        document_id + chunk_index
    """

    ground_truth = set()

    for chunk in item.get(
        "relevant_chunks",
        []
    ):

        ground_truth.add(
            (
                chunk["document_id"],
                chunk["chunk_index"]
            )
        )

    return ground_truth


def build_retrieved_ids(chunks):
    """
    Convert retrieved chunks into:

        (document_id, chunk_index)
    """

    return [
        (
            chunk.get("document_id"),
            chunk.get("chunk_index")
        )
        for chunk in chunks
    ]


# ============================================================
# HIT@K
# ============================================================

def calculate_hit_at_k(
    retrieved_ids,
    ground_truth,
    k
):

    top_k = retrieved_ids[:k]

    return int(
        any(
            chunk_id in ground_truth
            for chunk_id in top_k
        )
    )


# ============================================================
# RECALL@K
# ============================================================

def calculate_recall_at_k(
    retrieved_ids,
    ground_truth,
    k
):

    if not ground_truth:
        return None

    top_k = set(
        retrieved_ids[:k]
    )

    relevant_retrieved = (
        top_k.intersection(
            ground_truth
        )
    )

    return (
        len(relevant_retrieved)
        / len(ground_truth)
    )


# ============================================================
# MRR@K
# ============================================================

def calculate_mrr_at_k(
    retrieved_ids,
    ground_truth,
    k
):

    for rank, chunk_id in enumerate(
        retrieved_ids[:k],
        start=1
    ):

        if chunk_id in ground_truth:

            return 1 / rank

    return 0.0


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    results = []

    total_hit = 0
    total_recall = 0.0
    total_mrr = 0.0

    evaluated_questions = 0


    print(
        "\n=============================================="
    )

    print(
        "       RERANKING EVALUATION"
    )

    print(
        "=============================================="
    )


    for index, item in enumerate(
        dataset,
        start=1
    ):

        question_id = item["id"]

        question = item["question"]

        case_id = item["case_id"]

        ground_truth = build_ground_truth(
            item
        )


        # ----------------------------------------------------
        # Skip questions with no ground truth
        # ----------------------------------------------------

        if not ground_truth:

            print(
                f"\n{question_id}: "
                "Skipped — no ground truth."
            )

            continue


        print(
            f"\nEvaluating "
            f"{index}/{len(dataset)}: "
            f"{question_id}"
        )


        # ----------------------------------------------------
        # Stage 1:
        # Existing dense retrieval
        # ----------------------------------------------------

        retrieved_chunks = rag_service.retrieve(
            question=question,
            case_id=case_id,
            top_k=RETRIEVAL_K
        )


        # ----------------------------------------------------
        # Stage 2:
        # Cross-encoder reranking
        # ----------------------------------------------------

        reranked_chunks = reranker.rerank(
            question=question,
            documents=retrieved_chunks,
            top_k=RERANK_K
        )


        # ----------------------------------------------------
        # Convert to IDs
        # ----------------------------------------------------

        reranked_ids = build_retrieved_ids(
            reranked_chunks
        )


        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        hit = calculate_hit_at_k(
            retrieved_ids=reranked_ids,
            ground_truth=ground_truth,
            k=RERANK_K
        )

        recall = calculate_recall_at_k(
            retrieved_ids=reranked_ids,
            ground_truth=ground_truth,
            k=RERANK_K
        )

        mrr = calculate_mrr_at_k(
            retrieved_ids=reranked_ids,
            ground_truth=ground_truth,
            k=RERANK_K
        )


        # ----------------------------------------------------
        # Accumulate
        # ----------------------------------------------------

        total_hit += hit

        total_recall += recall

        total_mrr += mrr

        evaluated_questions += 1


        # ----------------------------------------------------
        # Save detailed result
        # ----------------------------------------------------

        result = {
            "id": question_id,
            "question": question,
            "case_id": case_id,
            "ground_truth": [
                {
                    "document_id": document_id,
                    "chunk_index": chunk_index
                }
                for document_id, chunk_index
                in ground_truth
            ],
            "reranked_chunks": [
                {
                    "document_id": chunk.get(
                        "document_id"
                    ),
                    "chunk_index": chunk.get(
                        "chunk_index"
                    ),
                    "page_number": chunk.get(
                        "page_number"
                    ),
                    "qdrant_score": chunk.get(
                        "score"
                    ),
                    "rerank_score": chunk.get(
                        "rerank_score"
                    )
                }
                for chunk in reranked_chunks
            ],
            "hit_at_5": hit,
            "recall_at_5": recall,
            "mrr_at_5": mrr
        }


        results.append(result)


        print(
            f"Hit@5: {hit}"
        )

        print(
            f"Recall@5: {recall:.4f}"
        )

        print(
            f"MRR@5: {mrr:.4f}"
        )


    # ========================================================
    # FINAL METRICS
    # ========================================================

    if evaluated_questions:

        hit_at_5 = (
            total_hit
            / evaluated_questions
        )

        recall_at_5 = (
            total_recall
            / evaluated_questions
        )

        mrr_at_5 = (
            total_mrr
            / evaluated_questions
        )

    else:

        hit_at_5 = 0.0
        recall_at_5 = 0.0
        mrr_at_5 = 0.0


    # ========================================================
    # OUTPUT
    # ========================================================

    output = {
        "retrieval_k": RETRIEVAL_K,
        "rerank_k": RERANK_K,
        "evaluated_questions": evaluated_questions,
        "hit_at_5": hit_at_5,
        "recall_at_5": recall_at_5,
        "mrr_at_5": mrr_at_5,
        "results": results
    }


    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )


    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    print(
        "\n=============================================="
    )

    print(
        "       RERANKING RESULTS"
    )

    print(
        "=============================================="
    )

    print(
        f"Questions evaluated: "
        f"{evaluated_questions}"
    )

    print(
        f"Hit@5: "
        f"{hit_at_5:.4f}"
    )

    print(
        f"Recall@5: "
        f"{recall_at_5:.4f}"
    )

    print(
        f"MRR@5: "
        f"{mrr_at_5:.4f}"
    )

    print(
        f"\nDetailed results saved to:"
    )

    print(
        OUTPUT_PATH
    )

    print(
        "==============================================\n"
    )


if __name__ == "__main__":
    main()