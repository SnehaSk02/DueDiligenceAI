import json
import sys
from pathlib import Path
import time
import re

# ---------------------------------------------------------
# 1. Add project root to Python path
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# 2. Import the actual LangGraph pipeline
# ---------------------------------------------------------

from backend.app.agents.graph import due_diligence_graph
from backend.app.services.llm_service import LLMService

# ---------------------------------------------------------
# 3. Configuration
# ---------------------------------------------------------

DATASET_PATH = PROJECT_ROOT / "evaluation" / "dataset.json"

RESULTS_PATH = PROJECT_ROOT / "evaluation" / "answer_results.json"


# ---------------------------------------------------------
# 4. Load evaluation dataset
# ---------------------------------------------------------

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    dataset = json.load(file)

def invoke_graph_with_retry(
    question: str,
    case_id: int,
    max_retries: int = 4
):
    for attempt in range(max_retries + 1):

        try:
            return due_diligence_graph.invoke({
                "question": question,
                "case_id": case_id
            })

        except Exception as e:

            error_text = str(e)
            lower_error = error_text.lower()

            is_rate_limit = (
                "429" in lower_error
                or "rate_limit_exceeded" in lower_error
                or "rate limit" in lower_error
            )

            if not is_rate_limit:
                raise

            if attempt == max_retries:
                raise

            match = re.search(
                r"try again in ([\d.]+)s",
                error_text,
                re.IGNORECASE
            )

            if match:
                wait_time = float(match.group(1)) + 1
            else:
                wait_time = min(5 * (2 ** attempt), 30)

            print(
                f"\nGroq rate limit encountered."
                f"\nRetry {attempt + 1}/{max_retries}"
                f"\nWaiting {wait_time:.1f} seconds..."
            )

            time.sleep(wait_time)

#----------------------------------------------------------
# Evaluate answer quality
#----------------------------------------------------------

def evaluate_answer_quality(question: str,
                            reference_answer: str,
                            generated_answer: str,
                            max_retries: int =4)->dict:
                                prompt = f"""
                        You are an answer-quality evaluator for a financial due-diligence RAG system.

                        Evaluate the generated answer against the reference answer.

                        Evaluate TWO dimensions independently:

                        1. Correctness
                        2. Completeness

                        CORRECTNESS:
                        - 1.0 = Fully factually correct.
                        - 0.5 = Mostly correct but contains a minor factual issue or imprecision.
                        - 0.0 = Contains a material factual error, contradiction, wrong number,
                            wrong unit, or misleading claim.

                        COMPLETENESS:
                        - 1.0 = Covers all important information required by the question.
                        - 0.5 = Answers the main question but misses one or more important details.
                        - 0.0 = Misses a major part of the requested information.

                        Important rules:
                        - Pay close attention to numerical values, currencies, units,
                        percentages, dates, and direction of changes.
                        - Do not require identical wording.
                        - Paraphrasing is acceptable.
                        - Do not penalize an answer merely because it is shorter.
                        - Judge whether the important factual information is present.
                        - Do not use outside knowledge.
                        - Base your evaluation only on the question, reference answer,
                        and generated answer.
                        - Return valid JSON only.
                        - Do not include markdown or additional text.

                        Question:
                        {question}

                        Reference answer:
                        {reference_answer}

                        Generated answer:
                        {generated_answer}

                        Return exactly this JSON structure:

                        {{
                            "correctness_score": 0.0,
                            "completeness_score": 0.0,
                            "correctness_reason": "string",
                            "completeness_reason": "string"
                        }}
                        """
                                llm_service = LLMService()
                                for attempt in range(max_retries+1):
                                    try:
                                          response = llm_service.generate_judge_response(prompt = prompt)
                                          result= json.loads(response)
                                          required_keys = {
                                               "correctness_score",
                                               "completeness_score",
                                               "correctness_reason",
                                               "completeness_reason"
                                          }
                                          if not required_keys.issubset(result.keys()):
                                               raise ValueError("LLM judge returned an invalid response schema.")

                                          if result["correctness_score"] not in {0.0,0.5,1.0}:
                                               raise ValueError("Invalid correctness score.")
                                          if result["completeness_score"] not in {0.0,0.5,1.0}:
                                               raise ValueError("Invalid completeness score.")
                                          return result
                                    except Exception as e:
                                        error_text = str(e)
                                        lower_error = error_text.lower()
                                        is_rate_limit = (
                                              "429" in lower_error or "rate limit exceeded" in lower_error
                                              or "rate limit" in lower_error
                                         )
                                        if not  is_rate_limit:
                                            raise
                                        if attempt == max_retries:
                                            raise
                                        match = re.search(r"try again in ([\d.]+)s",
                                                          error_text,
                                                          re.IGNORECASE)

                                        if match:
                                             wait_time = float(match.group(1))+1
                                        else:
                                             wait_time = min(5*(2** attempt), 30)
                                        print(
                                            f"\nJudge rate limit encountered."
                                            f"\nRetry {attempt + 1}/{max_retries}"
                                            f"\nWaiting {wait_time:.1f} seconds..."
                                        )

                                        time.sleep(wait_time) 
    
# ---------------------------------------------------------
# 5. Evaluate one question
# ---------------------------------------------------------
def evaluate_question(item):

    question_id = item["id"]
    question = item["question"]
    case_id = item["case_id"]
    reference_answer = item["reference_answer"]
    expected_routes = item.get("expected_routes", [])

    print("\n----------------------------------------------")
    print(f"Evaluating {question_id}")
    print(f"Question: {question}")
    print("----------------------------------------------")

    result = invoke_graph_with_retry(
        question=question,
        case_id=case_id
    )

    generated_answer = result.get("answer", "")

    print("\nGenerated answer:")
    print(generated_answer)

    actual_routes = result.get("routes", [])

    routing_correct = (
        set(actual_routes) == set(expected_routes)
    )

    # --------------------------------------------------
    # Answer quality evaluation
    # --------------------------------------------------

    quality_result = None

    # Q15 is intentionally unanswerable,
    # so it is evaluated through abstention instead.
    if question_id != "q15":

        print("\nEvaluating answer quality...")

        quality_result = evaluate_answer_quality(
            question=question,
            reference_answer=reference_answer,
            generated_answer=generated_answer
        )

        print(
            f"Correctness: "
            f"{quality_result['correctness_score']}"
        )

        print(
            f"Completeness: "
            f"{quality_result['completeness_score']}"
        )

        print(
            f"Correctness reason: "
            f"{quality_result['correctness_reason']}"
        )

        print(
            f"Completeness reason: "
            f"{quality_result['completeness_reason']}"
        )

    # --------------------------------------------------
    # Abstention evaluation
    # --------------------------------------------------

    abstention_expected = (
        question_id == "q15"
    )

    abstention_detected = (
        "information is not available"
        in generated_answer.lower()
    )

    # --------------------------------------------------
    # Return evaluation result
    # --------------------------------------------------

    return {
        "id": question_id,
        "question": question,
        "expected_routes": expected_routes,
        "actual_routes": actual_routes,
        "routing_correct": routing_correct,
        "reference_answer": reference_answer,
        "generated_answer": generated_answer,
        "answer_quality": quality_result,
        "abstention_expected": abstention_expected,
        "abstention_detected": abstention_detected,
        "retrieved_evidence": result.get("retrieved_evidence", [])
    }
# def evaluate_question(item):

#     question_id = item["id"]
#     question = item["question"]
#     case_id = item["case_id"]
#     reference_answer = item["reference_answer"]
#     expected_routes = item.get("expected_routes", [])

#     print("\n----------------------------------------------")
#     print(f"Evaluating {question_id}")
#     print(f"Question: {question}")
#     print("----------------------------------------------")

#     result = invoke_graph_with_retry(
#             question= question,
#             case_id = case_id)

#     generated_answer = result.get("answer", "")
#     print("\nGenerated answer:")
#     print(generated_answer)
#     quality_result = None

#     if question_id != "q15":
#         print("\nEvaluating answer quality...")

#         quality_result = evaluate_answer_quality(
#             question=question,
#             reference_answer=reference_answer,
#             generated_answer=generated_answer
#         )

#         print(f"Correctness: {quality_result['correctness_score']}")
#         print(f"Completeness: {quality_result['completeness_score']}")
#         print(
#             f"Correctness reason: "
#             f"{quality_result['correctness_reason']}"
#         )
#         print(
#             f"Completeness reason: "
#             f"{quality_result['completeness_reason']}"
#         )

#     actual_routes = result.get("routes", [])

#     routing_correct = (
#         set(actual_routes) == set(expected_routes)
#     )

#     # --------------------------------------------------
#     # Answer quality evaluation
#     # --------------------------------------------------

#     quality_result = None

#     # Q15 is intentionally unanswerable,
#     # so it is evaluated through abstention instead.
#     if question_id != "q15":

#         print("\nEvaluating answer quality...")

#         quality_result = evaluate_answer_quality(
#             question=question,
#             reference_answer=reference_answer,
#             generated_answer=generated_answer
#         )

#         print(
#             f"Correctness: "
#             f"{quality_result['correctness_score']}"
#         )

#         print(
#             f"Completeness: "
#             f"{quality_result['completeness_score']}"
#         )

#         print(
#             f"Correctness reason: "
#             f"{quality_result['correctness_reason']}"
#         )

#         print(
#             f"Completeness reason: "
#             f"{quality_result['completeness_reason']}"
#         )

#     # --------------------------------------------------
#     # Existing abstention evaluation
#     # --------------------------------------------------

#     abstention_expected = (
#         question_id == "q15"
#     )

#     abstention_detected = (
#         "information is not available"
#         in generated_answer.lower()
#     )

#     # --------------------------------------------------
#     # Return evaluation result
#     # --------------------------------------------------

#     return {
#         "id": question_id,
#         "question": question,
#         "expected_routes": expected_routes,
#         "actual_routes": actual_routes,
#         "routing_correct": routing_correct,
#         "reference_answer": reference_answer,
#         "generated_answer": generated_answer,
#         "answer_quality": quality_result,
#         "abstention_expected": abstention_expected,
#         "abstention_detected": abstention_detected
#     }

#     # routes = result.get("routes", [])
#     # sources = result.get("sources", [])

#     # # -----------------------------------------------------
#     # # Check expected abstention
#     # # -----------------------------------------------------

#     # relevant_chunks = item.get("relevant_chunks", [])

#     # expected_unanswerable = len(relevant_chunks) == 0

#     # abstention_detected = (
#     #     "information is not available"
#     #     in generated_answer.lower()
#     # )

#     # if expected_unanswerable:
#     #     abstention_status = abstention_detected
#     # else:
#     #     abstention_status = None

#     # # -----------------------------------------------------
#     # # Print result
#     # # -----------------------------------------------------

#     # print("\nRoutes:")
#     # print(routes)

#     # print("\nGenerated Answer:")
#     # print(generated_answer)

#     # print("\nReference Answer:")
#     # print(item["reference_answer"])

#     # if expected_unanswerable:
#     #     print("\nExpected: Unanswerable")
#     #     print("Abstention detected:", abstention_detected)

#     # print("\nSources:")
#     # for source in sources:
#     #     print(source)

#     # # -----------------------------------------------------
#     # # Return evaluation record
#     # # -----------------------------------------------------

#     # return {
#     #     "id": question_id,
#     #     "question": question,
#     #     "case_id": case_id,
#     #     "expected_routes": item.get(
#     #         "expected_routes", []
#     #     ),
#     #     "actual_routes": routes,
#     #     "reference_answer": item["reference_answer"],
#     #     "generated_answer": generated_answer,
#     #     "sources": sources,
#     #     "expected_unanswerable": expected_unanswerable,
#     #     "abstention_detected": abstention_detected
#     #         if expected_unanswerable
#     #         else None,
#     #     "abstention_correct": abstention_status
#     # }


# ---------------------------------------------------------
# 6. Main evaluation
# ---------------------------------------------------------

def main():

    print("\n==============================================")
    print("          ANSWER EVALUATION")
    print("==============================================")

    print(f"Dataset: {DATASET_PATH}")

    results = []

    for item in dataset:

        try:

            result = evaluate_question(item)

            results.append(result)

        except Exception as e:

            print(
                f"\nERROR while evaluating "
                f"{item['id']}: {e}"
            )

            results.append({
                "id": item["id"],
                "question": item["question"],
                "status": "ERROR",
                "error": str(e)
            })

    # -----------------------------------------------------
    # 7. Routing evaluation
    # -----------------------------------------------------

    routing_results = [
        result
        for result in results
        if "actual_routes" in result
    ]

    correct_routes = 0

    for result in routing_results:

        expected = set(result["expected_routes"])
        actual = set(result["actual_routes"])

        if expected == actual:
            correct_routes += 1

    if routing_results:

        routing_accuracy = (
            correct_routes / len(routing_results)
        )

    else:

        routing_accuracy = 0.0

    # -----------------------------------------------------
    # 8. Abstention evaluation
    # -----------------------------------------------------

    unanswerable_results = [
        result
        for result in results
        if result.get("abstention_expected") is True
    ]

    correct_abstentions = sum(
        1
        for result in unanswerable_results
        if result.get("abstention_detected") is True
    )

    if unanswerable_results:

        abstention_accuracy = (
            correct_abstentions
            / len(unanswerable_results)
        )

    else:

        abstention_accuracy = 0.0

    # -----------------------------------------------------
    # 9. Print aggregate results
    # -----------------------------------------------------

    print("\n==============================================")
    print("          AGGREGATE RESULTS")
    print("==============================================")

    print(
        f"Questions evaluated: "
        f"{len(routing_results)}"
    )

    print(
        f"Routing accuracy: "
        f"{routing_accuracy:.4f}"
    )

    print(
        f"Unanswerable questions: "
        f"{len(unanswerable_results)}"
    )

    if unanswerable_results:

        print(
            f"Correct abstentions: "
            f"{correct_abstentions}/"
            f"{len(unanswerable_results)}"
        )

        print(
            f"Abstention accuracy: "
            f"{abstention_accuracy:.4f}"
        )

    # -----------------------------------------------------
    # 10. Save detailed results
    # -----------------------------------------------------

    evaluation_report = {
        "total_questions": len(dataset),
        "evaluated_questions": len(routing_results),
        "routing_accuracy": routing_accuracy,
        "unanswerable_questions": len(
            unanswerable_results
        ),
        "correct_abstentions": correct_abstentions,
        "abstention_accuracy": (
            abstention_accuracy
            if unanswerable_results
            else None
        ),
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
    print("        ANSWER EVALUATION COMPLETE")
    print("==============================================\n")


# ---------------------------------------------------------
# 11. Run evaluation
# ---------------------------------------------------------

if __name__ == "__main__":
    main()