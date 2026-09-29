from typing import List,Dict,Any

class TokenBudgetManager:
    def __init__(self,max_context_tokens:int =6000,max_chunk_tokens: int =1200):
        self.max_context_tokens = max_context_tokens
        self.max_chunk_tokens = max_chunk_tokens

    def estimate_tokens(self,text:str)->int:
        if not text:
            return 0
        return max(1,len(text)//4)

    def truncate_text(self,text:str,max_tokens:int)->str:
        """Truncate text so that its estimated token count stays within the specified limit."""
        if not text:
            return ""
        max_characters =max_tokens*4
        if len(text)<= max_characters:
            return text
        return text[:max_characters]

    def prepare_chunks(self,chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limit the size of individual retrieved chunks.
        """

        prepared_chunks = []

        for chunk in chunks:

            updated_chunk = chunk.copy()

            text = updated_chunk.get("text", "")

            updated_chunk["original_token_estimate"] = (self.estimate_tokens(text))

            updated_chunk["text"] = self.truncate_text(
                text=text,
                max_tokens=self.max_chunk_tokens)

            updated_chunk["token_estimate"] = (self.estimate_tokens(updated_chunk["text"]))

            prepared_chunks.append(updated_chunk)

        return prepared_chunks

    def build_context(self,chunks: List[Dict[str, Any]]) -> str:
        """
        Build context while respecting the overall
        context token budget.
        """

        if not chunks:
            return ""

        context_parts = []
        total_tokens = 0

        for index, chunk in enumerate(chunks, start=1):

            text = chunk.get("text", "")

            if not text:
                continue

            chunk_text = (
                f"[Evidence {index}]\n"
                f"Document ID: {chunk.get('document_id')}\n"
                f"Document Type: {chunk.get('document_type')}\n"
                f"Page: {chunk.get('page_number')}\n"
                f"Content Type: {chunk.get('content_type')}\n"
                f"Content:\n{text}"
            )

            chunk_tokens = self.estimate_tokens(
                chunk_text
            )

            if (
                total_tokens + chunk_tokens
                > self.max_context_tokens
            ):
                remaining_tokens = (
                    self.max_context_tokens
                    - total_tokens
                )

                if remaining_tokens <= 0:
                    break

                chunk_text = self.truncate_text(
                    chunk_text,
                    remaining_tokens
                )

                context_parts.append(chunk_text)

                total_tokens += self.estimate_tokens(
                    chunk_text
                )

                break

            context_parts.append(chunk_text)

            total_tokens += chunk_tokens

        return "\n\n".join(context_parts)

    def get_usage(self,text: str) -> Dict[str, int]:
        """
        Return approximate token usage information.
        """

        estimated_tokens = self.estimate_tokens(text)

        return {
            "characters": len(text) if text else 0,
            "estimated_tokens": estimated_tokens,
            "max_context_tokens": self.max_context_tokens,
            "remaining_tokens": max(
                0,
                self.max_context_tokens - estimated_tokens
            )
        }


token_budget_manager = TokenBudgetManager()

    