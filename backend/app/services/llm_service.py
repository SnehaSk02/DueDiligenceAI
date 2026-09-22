import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    def generate_answer(
            self,
            question:str,
            context:str
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
        response = self.client.chat.completions.create(
            model = self.model,
            messages=[
                {
                    "role" : "user",
                    "content" : prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content.strip()

    def generate_judge_response(self, prompt:str)-> str:
        response = self.client.chat.completions.create(
            model = self.model,
            messages=[
                {
                    "role":"user",
                    "content": prompt
                }
            ],
            temperature=0
        )    
        return response.choices[0].message.content.strip()

    