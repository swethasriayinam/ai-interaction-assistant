from langchain_core.tools import tool
from database import AsyncSessionLocal
from models import Interaction
from langchain_groq import ChatGroq
from sqlalchemy import select
import json
from dotenv import load_dotenv

load_dotenv()

# Use the stable 8b model for logic extraction
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

@tool
async def log_interaction(chat_message: str):
    """Save a new HCP interaction."""
    prompt = f"Extract interaction fields from: '{chat_message}'. Return ONLY raw JSON with keys: hcp_name, interaction_type, topics, outcome."
    res = await llm.ainvoke(prompt)
    
    try:
        # Remove markdown and load JSON
        cleaned = res.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        
        # FIX: Ensure 'topics' is a string, not a list
        topics_value = data.get("topics")
        if isinstance(topics_value, list):
            topics_value = ", ".join(topics_value)

        async with AsyncSessionLocal() as db:
            # We use a try/except block inside the tool to catch database errors
            try:
                new_entry = Interaction(
                    hcp_name=data.get("hcp_name"),
                    interaction_type=data.get("interaction_type"),
                    topics=topics_value, # Now a string
                    outcome=data.get("outcome")
                )
                db.add(new_entry)
                await db.commit()
                return f"SUCCESS: Interaction for {data['hcp_name']} has been saved."
            except Exception as db_err:
                await db.rollback()
                return f"DATABASE ERROR: {str(db_err)}"
                
    except Exception as e:
        return f"EXTRACTION ERROR: {str(e)}"
    
@tool
async def edit_interaction(hcp_name: str, updates: dict):
    """Updates the most recent interaction for an HCP by their name."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import func
        # This looks for the name anywhere in the string, ignoring upper/lower case
        # Example: 'smith' will find 'Dr. Smith'
        search_term = hcp_name.replace("Dr. ", "").replace("Dr.", "").strip()
        
        result = await db.execute(
            select(Interaction)
            .filter(func.lower(Interaction.hcp_name).contains(search_term.lower()))
            .order_by(Interaction.created_at.desc())
        )
        db_item = result.scalars().first()
        
        if db_item:
            # Apply updates to existing columns
            for k, v in updates.items():
                if hasattr(db_item, k):
                    setattr(db_item, k, v)
                else:
                    # If AI sends a field like 'time', we save it in the outcome
                    db_item.outcome = f"{db_item.outcome} | Updated {k}: {v}"
            
            await db.commit()
            return f"SUCCESS: I have updated the record for {db_item.hcp_name}."
        
        return f"FAILURE: Could not find any record containing the name '{hcp_name}'."

@tool
async def get_hcp_details(hcp_name: str):
    """Get the history and last interaction details for a specific HCP."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Interaction).filter(Interaction.hcp_name.contains(hcp_name)))
        item = result.scalars().first()
        return f"HCP: {item.hcp_name}, Last Topic: {item.topics}" if item else "No history found."

@tool
async def suggest_next_action(hcp_context: str):
    """Get AI suggestions for the next follow-up steps based on context."""
    res = await llm.ainvoke(f"Suggest next steps for: {hcp_context}")
    return res.content

@tool
async def generate_followup_email(hcp_name: str, topics: str):
    """Draft a professional follow-up email for an HCP."""
    res = await llm.ainvoke(f"Draft a professional follow-up email to {hcp_name} about {topics}.")
    return res.content

tools_list = [log_interaction, edit_interaction, get_hcp_details, suggest_next_action, generate_followup_email]