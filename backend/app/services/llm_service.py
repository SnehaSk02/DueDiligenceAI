import os
import time
from dotenv import load_dotenv
from groq import Groq
from typing import Dict, Any, Optional

load_dotenv()

class LLMService:
    def __init__(self, model: str = "openai/gpt-oss-120b",
        timeout: float = 30.0,
        max_retries: int = 2):
        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = Groq(api_key=self.api_key,
                           timeout=self.timeout)
        

    def generate(self,
                 prompt: str,
                 temperature: float = 0,
                 response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        

        last_exception = None

        for attempt in range(self.max_retries + 1):

            start_time = time.perf_counter()

            try:

                request_kwargs = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": temperature
                }

                if response_format is not None:
                    request_kwargs["response_format"] = response_format

                response = self.client.chat.completions.create(
                    **request_kwargs
                )

                end_time = time.perf_counter()

                usage = getattr(response, "usage", None)

                prompt_tokens = (
                    getattr(usage, "prompt_tokens", 0)
                    if usage
                    else 0
                )

                completion_tokens = (
                    getattr(usage, "completion_tokens", 0)
                    if usage
                    else 0
                )

                total_tokens = (
                    getattr(usage, "total_tokens", 0)
                    if usage
                    else 0
                )

                return {
                    "content": response.choices[0].message.content,
                    "model": self.model,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens
                    },
                    "latency_seconds": round(
                        end_time - start_time,
                        3
                    ),
                    "status": "success",
                    "attempts": attempt + 1
                }

            except Exception as exc:

                last_exception = exc

                print(
                    f"LLM request failed "
                    f"(attempt {attempt + 1}/"
                    f"{self.max_retries + 1}): {exc}"
                )

                # If this was the final attempt,
                # stop retrying.
                if attempt == self.max_retries:
                    break

                # Exponential backoff:
                # attempt 0 -> 1 second
                # attempt 1 -> 2 seconds
                wait_time = 2 ** attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        raise RuntimeError(
            f"LLM request failed after "
            f"{self.max_retries + 1} attempts."
        ) from last_exception

    def generate_answer(
        self,
        question: str,
        context: str
    ) -> str:

        prompt = f"""
You are an AI assistant for a document-based due diligence system.

Answer the user's question using ONLY the information provided
in the document context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent or assume facts.
3. If the answer cannot be found in the context, say:
   "The information is not available in the provided documents."
4. Give a concise, factual answer.
5. Preserve important numbers, dates, percentages, and financial figures.
6. Do not make investment recommendations.
7. Do not mention information that is not supported by the context.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

        result = self.generate(
            prompt=prompt,
            temperature=0
        )

        return result["content"].strip()

    def generate_judge_response(
        self,
        prompt: str
    ) -> str:

        result = self.generate(
            prompt=prompt,
            temperature=0
        )

        return result["content"].strip()