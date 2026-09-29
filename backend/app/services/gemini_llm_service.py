import os
import time
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiLLMService:

    def __init__(
        self,
        model: str = "gemini-3.5-flash-lite",
        timeout: float = 30.0,
        max_retries: int = 2
    ):
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = genai.Client(
            api_key=self.api_key
        )

    def generate(
        self,
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

                config_kwargs = {
                    "temperature": temperature
                }

                if response_format is not None:

                    if response_format.get("type") == "json_object":
                        config_kwargs["response_mime_type"] = (
                            "application/json"
                        )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        **config_kwargs
                    )
                )

                end_time = time.perf_counter()

                usage = getattr(
                    response,
                    "usage_metadata",
                    None
                )

                prompt_tokens = (
                    getattr(
                        usage,
                        "prompt_token_count",
                        0
                    )
                    if usage else 0
                )

                completion_tokens = (
                    getattr(
                        usage,
                        "candidates_token_count",
                        0
                    )
                    if usage else 0
                )

                total_tokens = (
                    getattr(
                        usage,
                        "total_token_count",
                        0
                    )
                    if usage else 0
                )

                return {
                    "content": response.text,
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
                    f"Gemini request failed "
                    f"(attempt {attempt + 1}/"
                    f"{self.max_retries + 1}): {exc}"
                )

                if attempt == self.max_retries:
                    break

                wait_time = 2 ** attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        raise RuntimeError(
            f"Gemini request failed after "
            f"{self.max_retries + 1} attempts."
        ) from last_exception