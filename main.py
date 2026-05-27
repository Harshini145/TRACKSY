"""
Tracksy Backend — FastAPI + MySQL
=================================
Run:  uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:  # pragma: no cover - optional dependency
    AsyncIOScheduler = None
    IntervalTrigger = None

from core.database import engine, Base, SessionLocal
from services.budget_service import run_budget_checks_for_all_users

# Import all models so SQLAlchemy registers them before create_all
import models.user  # noqa: F401

from routers import auth, expenses, budgets, categories, food_spots, notifications, users


# ── Scheduled job ─────────────────────────────────────────────────────────────

async def scheduled_budget_check():
    """Hourly job: check every user's budget and send emails if needed."""
    db = SessionLocal()
    try:
        await run_budget_checks_for_all_users(db)
    finally:
        db.close()


# ── App lifecycle ─────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler() if AsyncIOScheduler is not None else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try creating tables — if DB is unreachable, log and continue so
    # the food-spots endpoint (and other non-DB features) still work.
    db_available = True
    try:
        # simple connect check
        with engine.connect() as conn:
            Base.metadata.create_all(bind=engine)
    except Exception as e:
        db_available = False
        print(f"[WARN] Could not connect to DB: {e}. Continuing without DB.")

    # Start hourly budget check scheduler only when DB is available
    if db_available and scheduler is not None and IntervalTrigger is not None:
        scheduler.add_job(
            scheduled_budget_check,
            trigger=IntervalTrigger(hours=1),
            id="budget_check",
            replace_existing=True,
        )
        scheduler.start()
        print("[OK] Tracksy backend started -- scheduler running")
    else:
        print("[WARN] Scheduler disabled (DB unavailable or APScheduler missing)")

    yield

    if scheduler is not None:
        try:
            scheduler.shutdown()
            print("[STOP] Tracksy backend stopped")
        except Exception:
            print("[STOP] Tracksy backend stopped (scheduler shutdown failed)")
    else:
        print("[STOP] Tracksy backend stopped (no scheduler)")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Tracksy API",
    description="Expense & Budget Management — with smart alerts and food spot discovery",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — update origins to match your frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(categories.router)
app.include_router(food_spots.router)
app.include_router(notifications.router)
app.include_router(users.router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "app": "Tracksy API v1.0.0"}

# Serve frontend static files at /app/*
app.mount("/app", StaticFiles(directory=".", html=True), name="frontend")
