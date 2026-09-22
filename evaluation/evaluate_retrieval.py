import json
import sys
from pathlib import Path


# ---------------------------------------------------------
# 1. Add project root to Python path
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# 2. Import RAG service
# ---------------------------------------------------------

from backend.app.services.rag_services import RAGService


# ---------------------------------------------------------
# 3. Configuration
# ---------------------------------------------------------

DATASET_PATH = PROJECT_ROOT / "evaluation" / "dataset.json"

TOP_K = 5

RESULTS_PATH = PROJECT_ROOT / "evaluation" / "retrieval_results.json"


# ---------------------------------------------------------
# 4. Load evaluation dataset
# ---------------------------------------------------------

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    dataset = json.load(file)


# ---------------------------------------------------------
# 5. Helper function
# ---------------------------------------------------------

def get_chunk_id(chunk):
    """
    Creates the identifier used to compare
    retrieved chunks with ground-truth chunks.

    A chunk is identified by:
        document_id + chunk_index
    """

    return (
        chunk.get("document_id"),
        chunk.get("chunk_index")
    )


# ---------------------------------------------------------
# 6. Evaluate one question
# ---------------------------------------------------------

def evaluate_question(rag_service, item):
    question_id = item["id"]
    question = item["question"]
    case_id = item["case_id"]

    relevant_chunks = item.get("relevant_chunks", [])

    # -----------------------------------------------------
    # Unanswerable question
    # -----------------------------------------------------
    if not relevant_chunks:
        return {
            "id": question_id,
            "question": question,
            "status": "NO_GROUND_TRUTH",
            "retrieved_chunks": [],
            "hit_at_k": None,
            "recall_at_k": None,
            "mrr_at_k": None,
            "first_relevant_rank": None
        }

    # -----------------------------------------------------
    # Ground-truth chunk IDs
    # -----------------------------------------------------

    relevant_ids = {
        (
            chunk["document_id"],
            chunk["chunk_index"]
        )
        for chunk in relevant_chunks
    }

    # -----------------------------------------------------
    # Retrieve chunks using the actual RAG pipeline
    # -----------------------------------------------------

    retrieved_chunks = rag_service.retrieve(
        question=question,
        case_id=case_id,
        top_k=TOP_K
    )

    retrieved_ids = [
        get_chunk_id(chunk)
        for chunk in retrieved_chunks
    ]

    # -----------------------------------------------------
    # Find relevant chunks that were retrieved
    # -----------------------------------------------------

    retrieved_relevant_ids = (
        set(retrieved_ids) & relevant_ids
    )

    # -----------------------------------------------------
    # Hit@K
    #
    # 1 if at least one relevant chunk
    # appears in the top K.
    # Otherwise 0.
    # -----------------------------------------------------

    hit_at_k = (
        1 if retrieved_relevant_ids else 0
    )

    # -----------------------------------------------------
    # Recall@K
    #
    # Number of relevant chunks retrieved
    # divided by total relevant chunks.
    # -----------------------------------------------------

    recall_at_k = (
        len(retrieved_relevant_ids)
        / len(relevant_ids)
    )

    # -----------------------------------------------------
    # MRR@K
    #
    # Reciprocal rank of the FIRST relevant chunk.
    #
    # Example:
    # relevant chunk at rank 1 -> 1/1 = 1.0
    # relevant chunk at rank 2 -> 1/2 = 0.5
    # relevant chunk at rank 5 -> 1/5 = 0.2
    # -----------------------------------------------------

    relevant_ranks = []

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            relevant_ranks.append(rank)

    if relevant_ranks:
        first_relevant_rank = min(relevant_ranks)
        mrr_at_k = 1 / first_relevant_rank
    else:
        first_relevant_rank = None
        mrr_at_k = 0.0

    # -----------------------------------------------------
    # Store retrieved chunk information
    # -----------------------------------------------------

    retrieved_chunk_details = []

    for rank, chunk in enumerate(
        retrieved_chunks,
        start=1
    ):
        retrieved_chunk_details.append({
            "rank": rank,
            "document_id": chunk.get("document_id"),
            "chunk_index": chunk.get("chunk_index"),
            "page_number": chunk.get("page_number"),
            "content_type": chunk.get("content_type"),
            "score": chunk.get("score"),
            "is_relevant": (
                get_chunk_id(chunk) in relevant_ids
            )
        })

    return {
        "id": question_id,
        "question": question,
        "status": "EVALUATED",
        "relevant_chunks": [
            {
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"]
            }
            for chunk in relevant_chunks
        ],
        "retrieved_chunks": retrieved_chunk_details,
        "hit_at_k": hit_at_k,
        "recall_at_k": recall_at_k,
        "mrr_at_k": mrr_at_k,
        "first_relevant_rank": first_relevant_rank
    }


# ---------------------------------------------------------
# 7. Main evaluation
# ---------------------------------------------------------

def main():

    print("\n==============================================")
    print("       RETRIEVAL EVALUATION")
    print("==============================================")

    print(f"Dataset: {DATASET_PATH}")
    print(f"Top-K: {TOP_K}")

    print("\nLoading RAG service...")

    # IMPORTANT:
    # Create RAGService only once so that the
    # embedding model is loaded only once.
    rag_service = RAGService()

    results = []

    for item in dataset:

        print(
            f"\nEvaluating {item['id']}: "
            f"{item['question']}"
        )

        try:

            result = evaluate_question(
                rag_service,
                item
            )

            results.append(result)

            if result["status"] == "NO_GROUND_TRUTH":

                print(
                    "Status: Skipped "
                    "(no relevant ground-truth chunks)"
                )

            else:

                print(
                    f"Hit@{TOP_K}: "
                    f"{result['hit_at_k']}"
                )

                print(
                    f"Recall@{TOP_K}: "
                    f"{result['recall_at_k']:.4f}"
                )

                print(
                    f"MRR@{TOP_K}: "
                    f"{result['mrr_at_k']:.4f}"
                )

                print(
                    "First relevant rank:",
                    result["first_relevant_rank"]
                )

        except Exception as e:

            print(
                f"ERROR while evaluating "
                f"{item['id']}: {e}"
            )

            results.append({
                "id": item["id"],
                "question": item["question"],
                "status": "ERROR",
                "error": str(e)
            })

    # -----------------------------------------------------
    # 8. Calculate aggregate metrics
    # -----------------------------------------------------

    evaluated_results = [
        result
        for result in results
        if result["status"] == "EVALUATED"
    ]

    skipped_results = [
        result
        for result in results
        if result["status"] == "NO_GROUND_TRUTH"
    ]

    error_results = [
        result
        for result in results
        if result["status"] == "ERROR"
    ]

    if evaluated_results:

        average_hit = (
            sum(
                result["hit_at_k"]
                for result in evaluated_results
            )
            / len(evaluated_results)
        )

        average_recall = (
            sum(
                result["recall_at_k"]
                for result in evaluated_results
            )
            / len(evaluated_results)
        )

        average_mrr = (
            sum(
                result["mrr_at_k"]
                for result in evaluated_results
            )
            / len(evaluated_results)
        )

    else:

        average_hit = 0.0
        average_recall = 0.0
        average_mrr = 0.0

    # -----------------------------------------------------
    # 9. Print final results
    # -----------------------------------------------------

    print("\n==============================================")
    print("          AGGREGATE RESULTS")
    print("==============================================")

    print(
        f"Evaluated questions: "
        f"{len(evaluated_results)}"
    )

    print(
        f"Skipped questions: "
        f"{len(skipped_results)}"
    )

    print(
        f"Errors: "
        f"{len(error_results)}"
    )

    print(
        f"\nHit@{TOP_K}: "
        f"{average_hit:.4f}"
    )

    print(
        f"Recall@{TOP_K}: "
        f"{average_recall:.4f}"
    )

    print(
        f"MRR@{TOP_K}: "
        f"{average_mrr:.4f}"
    )

    # -----------------------------------------------------
    # 10. Save detailed evaluation results
    # -----------------------------------------------------

    evaluation_report = {
        "top_k": TOP_K,
        "total_questions": len(dataset),
        "evaluated_questions": len(evaluated_results),
        "skipped_questions": len(skipped_results),
        "error_questions": len(error_results),
        "metrics": {
            f"hit@{TOP_K}": average_hit,
            f"recall@{TOP_K}": average_recall,
            f"mrr@{TOP_K}": average_mrr
        },
        "results": results
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            evaluation_report,
            file,
            indent=2
        )

    print(
        f"\nDetailed results saved to:"
        f"\n{RESULTS_PATH}"
    )

    print("\n==============================================")
    print("       EVALUATION COMPLETE")
    print("==============================================\n")


# ---------------------------------------------------------
# 11. Run
# ---------------------------------------------------------

if __name__ == "__main__":
    main()