import json
import re
import time
from pathlib import Path

from backend.app.services.llm_service import LLMService


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "evaluation" / "answer_results.json"
OUTPUT_FILE = PROJECT_ROOT / "evaluation" / "answer_quality_results.json"


def evaluate_answer_quality(
    question: str,
    reference_answer: str,
    generated_answer: str,
    max_retries: int = 4
) -> dict:

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
- Treat reasonable rounding as correct when the rounded value represents
  the same underlying quantity and unit.
- For example, $128.5 billion can be considered consistent with
  $128.528 billion.
- A unit difference such as million vs billion is a material error even
  when the numerical digits are identical.
- Evaluate ALL factual claims in the generated answer, including
  additional claims that are not directly required by the question.
- Do not ignore an additional factual claim simply because it is unrelated
  to the main question.
- Do not require identical wording.
- Paraphrasing is acceptable.
- Do not penalize an answer merely because it is shorter.
- Judge whether the important factual information is present.
- Do not use outside knowledge.
- Base your evaluation only on the question, reference answer,
  and generated answer.
- Return valid JSON only.
- Do not include markdown or additional text.

QUESTION:
{question}

REFERENCE ANSWER:
{reference_answer}

GENERATED ANSWER:
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

    for attempt in range(max_retries + 1):

        try:

            response = llm_service.generate_judge_response(prompt)

            result = json.loads(response)

            required_keys = {
                "correctness_score",
                "completeness_score",
                "correctness_reason",
                "completeness_reason"
            }

            if not required_keys.issubset(result.keys()):
                raise ValueError(
                    "LLM judge returned an invalid response schema."
                )

            if result["correctness_score"] not in {0.0, 0.5, 1.0}:
                raise ValueError(
                    "Invalid correctness score."
                )

            if result["completeness_score"] not in {0.0, 0.5, 1.0}:
                raise ValueError(
                    "Invalid completeness score."
                )

            return result

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
                wait_time = min(
                    5 * (2 ** attempt),
                    30
                )

            print(
                f"\nJudge rate limit encountered."
                f"\nRetry {attempt + 1}/{max_retries}"
                f"\nWaiting {wait_time:.1f} seconds..."
            )

            time.sleep(wait_time)


def main():

    print("Loading saved evaluation results...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        saved_results = json.load(f)
    if isinstance(saved_results, dict):
        saved_results = saved_results["results"]

    quality_results = []

    for item in saved_results:

        question_id = item["id"]

        print("\n" + "=" * 70)
        print(f"Evaluating answer quality: {question_id}")
        print("=" * 70)

        # Q15 is intentionally unanswerable.
        # It is handled by abstention evaluation instead.
        if question_id == "q15":

            quality_results.append({
                "id": question_id,
                "answer_quality": None,
                "skipped": True,
                "reason": "Intentionally unanswerable question."
            })

            print("Skipped — intentionally unanswerable.")

            continue

        question = item["question"]
        reference_answer = item["reference_answer"]
        generated_answer = item["generated_answer"]

        result = evaluate_answer_quality(
            question=question,
            reference_answer=reference_answer,
            generated_answer=generated_answer
        )

        quality_results.append({
            "id": question_id,
            "question": question,
            "reference_answer": reference_answer,
            "generated_answer": generated_answer,
            "answer_quality": result,
            "skipped": False
        })

        print(
            f"Correctness: "
            f"{result['correctness_score']}"
        )

        print(
            f"Completeness: "
            f"{result['completeness_score']}"
        )

        print(
            f"Correctness reason: "
            f"{result['correctness_reason']}"
        )

        print(
            f"Completeness reason: "
            f"{result['completeness_reason']}"
        )

    # --------------------------------------------------
    # Aggregate metrics
    # --------------------------------------------------

    evaluated_results = [
        item
        for item in quality_results
        if not item["skipped"]
    ]

    correctness_scores = [
        item["answer_quality"]["correctness_score"]
        for item in evaluated_results
    ]

    completeness_scores = [
        item["answer_quality"]["completeness_score"]
        for item in evaluated_results
    ]

    average_correctness = (
        sum(correctness_scores)
        / len(correctness_scores)
    )

    average_completeness = (
        sum(completeness_scores)
        / len(completeness_scores)
    )

    print("\n" + "=" * 70)
    print("ANSWER QUALITY SUMMARY")
    print("=" * 70)

    print(
        f"Questions evaluated: "
        f"{len(evaluated_results)}"
    )

    print(
        f"Average correctness: "
        f"{average_correctness:.4f}"
    )

    print(
        f"Average completeness: "
        f"{average_completeness:.4f}"
    )

    # --------------------------------------------------
    # Save results
    # --------------------------------------------------

    final_results = {
        "questions_evaluated": len(evaluated_results),
        "average_correctness": average_correctness,
        "average_completeness": average_completeness,
        "results": quality_results
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            final_results,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nResults saved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()