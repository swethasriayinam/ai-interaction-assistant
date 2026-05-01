from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy import select, func
from database import AsyncSessionLocal
from models import Interaction
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


# ================= UTIL =================
def normalize(value):
    if isinstance(value, list):
        return ", ".join(value)
    return value or ""


# ================= GET HCP DETAILS =================
@tool
async def get_hcp_details(hcp_name: str):
    """Fetch HCP interaction history"""

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Interaction).filter(
                func.lower(Interaction.hcp_name).contains(hcp_name.lower())
            )
        )

        item = result.scalars().first()

        if not item:
            return "No history found."

        return {
            "hcp_name": item.hcp_name,
            "topics": item.topics,
            "outcome": item.outcome,
            "interaction_type": item.interaction_type,
            "notes": item.notes,
        }


# ================= EDIT INTERACTION =================
@tool
async def edit_interaction(hcp_name: str, updates: dict):
    """Update HCP interaction safely"""

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Interaction)
            .filter(func.lower(Interaction.hcp_name).contains(hcp_name.lower()))
            .order_by(Interaction.created_at.desc())
        )

        item = result.scalars().first()

        if not item:
            return "HCP not found."

        for k, v in updates.items():
            if hasattr(item, k):
                setattr(item, k, normalize(v))

        await db.commit()
        return f"Updated {item.hcp_name}"


# ================= EMAIL =================
@tool
async def generate_followup_email(hcp_name: str, topics: str):
    """Generate follow-up email"""

    topics = normalize(topics)

    res = await llm.ainvoke(f"""
Write a professional follow-up email.

Doctor: {hcp_name}
Topics: {topics}

Include:
- Subject
- Greeting
- Body
- Closing
""")

    return res.content


# ================= NEXT ACTION =================
@tool
async def suggest_next_action(hcp_context: str):
    """Suggest ONE CRM next action"""

    res = await llm.ainvoke(f"""
You are a CRM assistant.

Return ONLY ONE next action (1 sentence).

Context:
{hcp_context}
""")

    return res.content


tools_list = [
    get_hcp_details,
    edit_interaction,
    generate_followup_email,
    suggest_next_action
]