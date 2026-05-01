import json
import re
from tools import llm


def safe_json_parse(text: str):
    """
    Extracts JSON from LLM output safely.
    Handles markdown, bad formatting, etc.
    """

    # remove ```json blocks if present
    text = text.strip()
    text = re.sub(r"```json|```", "", text)

    try:
        return json.loads(text)
    except Exception:
        return None


def normalize(value):
    """Convert list → string safely"""
    if isinstance(value, list):
        return ", ".join(value)
    return value or ""


async def extract_interaction(message: str):

    prompt = f"""
You are a STRICT CRM intent classifier.

Return ONLY valid JSON.

RULES:
- No explanations
- No markdown
- No backticks

INTENTS:
create, update, fetch, email, next_action

RULES:
- met/discussed/saw → create
- update/change → update
- show/details/history → fetch
- write email/follow up email → email
- what should I do next → next_action

OUTPUT FORMAT:
{{
  "intent": "",
  "hcp_name": "",
  "topics": "",
  "outcome": "",
  "notes": ""
}}

Message:
{message}
"""

    res = await llm.ainvoke(prompt)

    data = safe_json_parse(res.content)

    if not data:
        return {
            "intent": "create",
            "hcp_name": "",
            "topics": "",
            "outcome": "",
            "notes": message
        }

    # 🔥 FORCE CLEAN TYPES (THIS FIXES YOUR BUGS)
    return {
        "intent": data.get("intent", "create"),
        "hcp_name": normalize(data.get("hcp_name")),
        "topics": normalize(data.get("topics")),
        "outcome": normalize(data.get("outcome")),
        "notes": normalize(data.get("notes", message))
    }