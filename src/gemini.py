import json

from google import genai
from google.genai import types


class GeminiService:

    def __init__(
        self,
        api_key,
        model
    ):

        self.enabled = bool(
            api_key
        )

        self.model = model

        self.client = (
            genai.Client(
                api_key=api_key
            )
            if self.enabled
            else None
        )

    def answer(
        self,
        question,
        context
    ):

        if not self.enabled:

            return (
                None,
                "GEMINI_API_KEY is not configured. "
                "Showing deterministic data answer instead."
            )

        prompt = f"""
You are a retail sales and inventory copilot.

Your job is to help a store manager make decisions.

IMPORTANT RULES:

1. Answer ONLY from the supplied evidence.
2. Never invent numbers.
3. Never invent products, stores, sales, weather,
   market conditions, supplier information, or other facts.
4. Every factual claim MUST cite an evidence ID.
5. Use citations exactly like [E1], [E2], etc.
6. If the evidence cannot answer the question,
   clearly say that the available data is insufficient.
7. Keep the answer concise and manager-friendly.
8. Separate assumptions from factual findings.
9. Recommendations must be supported by the supplied
   policy or data evidence.
10. Do not pretend unsupported external information exists.

Question:
{question}

Evidence:
{context}

Return valid JSON with exactly these keys:

{{
  "answer": "manager-friendly answer",
  "evidence_ids": ["E1", "E2"],
  "assumptions": [],
  "confidence": "high"
}}

confidence must be one of:

high
medium
low
"""

        try:

            response = (
                self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            )

            data = json.loads(
                response.text
            )

            return data, None

        except Exception as exc:

            return (
                None,
                (
                    "Model call failed safely: "
                    f"{type(exc).__name__}."
                )
            )

    def embed(self, texts):

        if not self.enabled:
            return None

        try:

            output = []

            for text in texts:

                response = (
                    self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=text
                    )
                )

                embedding = (
                    response
                    .embeddings[0]
                    .values
                )

                output.append(
                    embedding
                )

            return output

        except Exception:

            return None