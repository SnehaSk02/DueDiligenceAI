from typing import Dict,Any,Optional
from backend.app.services.llm_service import LLMService
from backend.app.services.gemini_llm_service import GeminiLLMService


class LLMGateway:
    def __init__(self,primary_llm:Optional[LLMService]=None,fallback_llm:Optional[GeminiLLMService]=None):
        self.primary_llm = primary_llm or LLMService()
        self.fallback_llm = fallback_llm or GeminiLLMService()

    def generate(self,
                 prompt:str,
                 temperature:float = 0,
                 response_format: Optional[Dict[str,Any]]=None)->Dict[str,Any]:
        try:
            result = self.primary_llm.generate(
                prompt=prompt,
                temperature=temperature,
                response_format=response_format
            )

            result["provider"] = "primary"

            return result
        except Exception as primary_error:
            print(
                f"Primary LLM failed: {primary_error}"
            )
            if self.fallback_llm is None:
                raise RuntimeError(
                    "Primary LLM failed and no fallback LLM is configured."
                )from primary_error

            try:
                result = self.fallback_llm.generate(
                    prompt=prompt,
                    temperature=temperature,
                    response_format=response_format
                )

                result["provider"] = "fallback"

                return result

            except Exception as fallback_error:

                print(
                    f"Fallback LLM failed: {fallback_error}"
                )

                raise RuntimeError(
                    f"Both primary and fallback LLMs failed. "
                    f"Primary error: {primary_error}. "
                    f"Fallback error: {fallback_error}"
                ) from fallback_error
gateway = LLMGateway()