from datetime import date
import json
from tools import llm   # ✅ IMPORTANT FIX


async def extract_interaction(text: str):

    prompt = f"""
You are a Medical CRM AI assistant.

Extract structured interaction data.

Return ONLY valid JSON.

Rules:
- Detect doctor names like "Dr. Rao", "Dr Rao", "Doctor Rao"
- If meeting implied → interaction_type = "Meeting"
- If today mentioned → use {date.today()}
- Infer outcome:
  good discussion → Positive
  normal discussion → Neutral
  problem → Negative

Fields:
hcp_name
interaction_type
date
topics
outcome
notes

Text:
{text}
"""

    response = await llm.ainvoke(prompt)

    try:
        cleaned = (
            response.content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        data = json.loads(cleaned)

    except Exception as e:
        print("Extraction error:", e)
        data = {}

    return data