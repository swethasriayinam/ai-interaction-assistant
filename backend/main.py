from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

import models
import database
from extractor import extract_interaction
from tools import (
    get_hcp_details,
    edit_interaction,
    generate_followup_email,
    suggest_next_action
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def calculate_score(data):
    score = 50

    outcome = (data.get("outcome") or "").lower()
    topics = (data.get("topics") or "").lower()

    if "positive" in outcome or "interested" in outcome:
        score += 25
    elif "negative" in outcome or "not interested" in outcome:
        score -= 25

    if "diabetes" in topics:
        score += 10

    return max(0, min(100, score))


@app.post("/chat")
async def chat(data: dict):

    extracted = await extract_interaction(data["message"])

    if not extracted.get("hcp_name"):
        return {"response": "Could not detect HCP name"}

    intent = extracted.get("intent", "create")


    # ================= FETCH =================
    if intent == "fetch":
        result = await get_hcp_details.ainvoke({
            "hcp_name": extracted["hcp_name"]
        })

        if isinstance(result, dict):
            return {
                "response": f"""
HCP: {result['hcp_name']}
Topics: {result['topics']}
Outcome: {result['outcome']}
Last Interaction Type: {result['interaction_type']}
""",
                "extracted_data": extracted
            }

        return {"response": result, "extracted_data": extracted}


    # ================= UPDATE =================
    if intent == "update":
        result = await edit_interaction.ainvoke({
            "hcp_name": extracted["hcp_name"],
            "updates": extracted
        })

        return {"response": result, "extracted_data": extracted}


    # ================= EMAIL =================
    if intent == "email":
        result = await generate_followup_email.ainvoke({
            "hcp_name": extracted["hcp_name"],
            "topics": extracted.get("topics", "")
        })

        return {"response": result, "extracted_data": extracted}


    # ================= NEXT ACTION =================
    score = calculate_score(extracted)

    context = f"""
HCP: {extracted['hcp_name']}
Topics: {extracted.get('topics')}
Outcome: {extracted.get('outcome')}
Score: {score}
"""

    suggestion = await suggest_next_action.ainvoke({
        "hcp_context": context
    })

    return {
        "response": suggestion,
        "score": score,
        "extracted_data": extracted
    }


@app.post("/log-interaction")
async def log_interaction(data: dict, db: AsyncSession = Depends(database.get_db)):

    if not data.get("hcp_name"):
        raise HTTPException(400, "HCP name required")

    new = models.Interaction(
        hcp_name=data["hcp_name"],
        interaction_type=data.get("interaction_type", "Meeting"),
        topics=data.get("topics", ""),
        outcome=data.get("outcome", "Neutral"),
        notes=data.get("notes", "")
    )

    db.add(new)
    await db.commit()

    return {"message": "saved"}