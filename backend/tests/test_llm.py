from backend.app.services.llm_service import LLMService


llm = LLMService()

context = """
The company reported strong revenue growth in 2025,
with total revenue increasing by 18% compared with
the previous financial year.
"""

question = "What happened to the company's revenue in 2025?"

answer = llm.generate_answer(
    question=question,
    context=context
)

print("\nAnswer:")
print(answer)