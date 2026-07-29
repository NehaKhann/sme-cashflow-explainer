import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, dispose_db
from .routers import analysis, reports, auth, chat

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await dispose_db()


app = FastAPI(
    title="SME Cash-Flow Explainer",
    description="Turns raw bank transaction exports into an underwriter-readable "
                 "cash-flow risk narrative, with every figure traceable to a computed number.",
    version="1.0.0",
    lifespan=lifespan,
)

cors_raw = os.getenv("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()] if cors_raw else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["http://localhost:5173"],
    allow_credentials=bool(cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "SME Cash-Flow Explainer API. POST a transaction CSV to /api/analyze."}
