"""Real Gemini API client with LangSmith tracing."""

import os
import json
import re
import google.generativeai as genai
from langsmith import traceable


class GeminiClient:
    """Production Gemini client using google-generativeai SDK."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)

        self.flash = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        )
        self.pro = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1024,
            ),
        )

    @traceable(name="gemini_flash_call")
    async def generate_flash(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generate text using Gemini Flash."""
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        response = await self.flash.generate_content_async(full_prompt)
        return response.text

    @traceable(name="gemini_pro_evaluate")
    async def evaluate_pro(self, prompt: str, system_instruction: str | None = None) -> str:
        """Evaluate using Gemini Pro (evaluator role)."""
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        response = await self.pro.generate_content_async(full_prompt)
        return response.text

    @traceable(name="gemini_flash_json")
    async def generate_json(self, prompt: str, system_instruction: str | None = None) -> dict:
        """Generate structured JSON output from Gemini Flash."""
        json_instruction = (system_instruction or "") + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no code fences, just the JSON object."
        raw = await self.generate_flash(prompt, json_instruction)

        # Try to extract JSON from response
        # Remove markdown code fences if present
        cleaned = re.sub(r'```(?:json)?\s*', '', raw)
        cleaned = cleaned.strip()

        # Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"No valid JSON found in response: {raw[:500]}")
    @traceable(name="gemini_embed")
    async def embed(self, text: str, task_type: str = "retrieval_query") -> list[float]:
        """Generate embeddings using Gemini."""
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type=task_type
        )
        return result['embedding']

    @traceable(name="gemini_embed_batch")
    async def embed_batch(self, texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
        """Generate batch embeddings using Gemini."""
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texts,
            task_type=task_type
        )
        return result['embedding']
