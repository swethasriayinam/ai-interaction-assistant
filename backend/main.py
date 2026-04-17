from fastapi import FastAPI, Depends
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert
from pydantic import BaseModel, ConfigDict

import models
import database
from extractor import extract_interaction

app = FastAPI()

# ====================== REQUEST MODELS ======================

class ChatRequest(BaseModel):
    message: str


class LogInteractionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hcp_name: str
    interaction_type: str | None = None
    date: str | None = None
    time: str | None = None
    attendees: str | None = None
    topics: str | None = None
    materials_shown: str | None = None
    samples_distributed: str | None = None
    outcome: str | None = None
    follow_up: str | None = None
    notes: str | None = None


# ====================== CORS ======================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================== STARTUP ======================

@app.on_event("startup")
async def startup():
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


# ====================== CHAT ======================

@app.post("/chat")
async def chat(data: ChatRequest):

    print("User Message:", data.message)

    extracted = await extract_interaction(data.message)

    print("AI Extracted Data:", extracted)

    # Prevent empty extraction
    if not extracted or not extracted.get("hcp_name"):
        return {
            "response": "I couldn't identify the doctor name. Please try again.",
            "extracted_data": {}
        }

    return {
        "response": "Interaction extracted successfully",
        "extracted_data": extracted
    }

# ====================== LOG INTERACTION ======================

@app.post("/log-interaction")
async def log_interaction(
    data: LogInteractionRequest,
    db: AsyncSession = Depends(database.get_db)
):

    # ==============================
    # DEBUG → CHECK WHAT FRONTEND SENDS
    # ==============================
    print("\n===== INTERACTION RECEIVED =====")
    print(data)
    print("===============================\n")

    # ❌ Prevent empty interaction saving
    if not data.hcp_name or data.hcp_name.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="HCP name is required"
        )

    parsed_date = None
    parsed_time = None

    # ==============================
    # SAFE DATE PARSING
    # ==============================
    if data.date and data.date != "string":
        try:
            parsed_date = datetime.strptime(
                data.date,
                "%Y-%m-%d"
            ).date()
        except Exception:
            print("Invalid date format received")

    # ==============================
    # SAFE TIME PARSING
    # ==============================
    if data.time and data.time != "string":
        try:
            parsed_time = datetime.strptime(
                data.time,
                "%H:%M"
            ).time()
        except Exception:
            print("Invalid time format received")

    # ==============================
    # INSERT INTO DATABASE
    # ==============================
    stmt = insert(models.Interaction).values(
        hcp_name=data.hcp_name.strip(),
        interaction_type=data.interaction_type or "Meeting",
        date=parsed_date,
        time=parsed_time,
        attendees=data.attendees or "",
        topics=data.topics or "",
        materials_shown=data.materials_shown or "",
        samples_distributed=data.samples_distributed or "",
        outcome=data.outcome or "Neutral",
        follow_up=data.follow_up or "",
        notes=data.notes or ""
    )

    await db.execute(stmt)
    await db.commit()

    print("✅ Interaction saved successfully")

    return {
        "message": "Interaction saved successfully"
    }
# ====================== INSIGHTS ======================

@app.get("/insights")
async def insights(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(func.count(models.Interaction.id)))
    return {"total": result.scalar()}


# ====================== GET ALL ======================

@app.get("/interactions")
async def get_interactions(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Interaction))
    return result.scalars().all()