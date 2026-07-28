import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analysis

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SME Cash-Flow Explainer",
    description="Turns raw bank transaction exports into an underwriter-readable "
                 "cash-flow risk narrative, with every figure traceable to a computed number.",
    version="1.0.0",
)

# Loosen for local/demo use; tighten to your actual frontend origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "SME Cash-Flow Explainer API. POST a transaction CSV to /api/analyze."}
