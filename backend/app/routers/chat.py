import os
import json
import logging
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from ..auth import get_current_user
from ..db_models import User
from ..rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "ollama")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

DEFAULT_MODEL = os.getenv("CHAT_MODEL", "ledger-chatbot")
GROQ_DEFAULT = os.getenv("CHAT_MODEL", "llama-3.3-70b-versatile")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    model: str | None = None

    @field_validator("message")
    @classmethod
    def message_max_length(cls, v: str) -> str:
        if len(v) > 5000:
            raise ValueError("Message exceeds maximum length of 5000 characters.")
        return v


def _build_messages(req: ChatRequest) -> list[dict]:
    msgs = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in req.history]
    msgs.append({"role": "user", "content": req.message})
    return msgs


@router.post("")
@limiter.limit("20/minute")
async def chat(request: Request, req: ChatRequest, current_user: User = Depends(get_current_user)) -> StreamingResponse:
    if CHAT_PROVIDER == "groq":
        if not GROQ_API_KEY:
            return StreamingResponse(
                _error_stream("GROQ_API_KEY is not set. Set CHAT_PROVIDER=ollama or provide a GROQ_API_KEY."),
                media_type="text/event-stream",
                headers=_sse_headers(),
            )
        return StreamingResponse(
            _stream_groq(req.model or GROQ_DEFAULT, req),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )

    return StreamingResponse(
        _stream_ollama(req.model or DEFAULT_MODEL, req),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


async def _error_stream(msg: str) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps({'error': msg})}\n\n"
    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------

async def _stream_ollama(model: str, req: ChatRequest) -> AsyncGenerator[str, None]:
    url = f"{OLLAMA_BASE}/api/chat"
    payload = {
        "model": model,
        "messages": _build_messages(req),
        "stream": True,
        "options": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 512},
    }

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    logger.error(f"Ollama error ({resp.status_code}): {error_text}")
                    yield f"data: {json.dumps({'error': f'Ollama returned {resp.status_code}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk:
                            content = chunk["message"].get("content", "")
                            if content:
                                yield f"data: {json.dumps({'text': content})}\n\n"
                        if chunk.get("done"):
                            yield "data: [DONE]\n\n"
                    except json.JSONDecodeError:
                        continue

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama. Is it running?")
            yield f"data: {json.dumps({'error': 'Cannot connect to Ollama. Make sure ollama is running (ollama serve).'})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception:
            logger.exception("Ollama stream error")
            yield f"data: {json.dumps({'error': 'An internal error occurred.'})}\n\n"
            yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# GROQ provider
# ---------------------------------------------------------------------------

async def _stream_groq(model: str, req: ChatRequest) -> AsyncGenerator[str, None]:
    try:
        from groq import AsyncGroq
    except ImportError:
        yield f"data: {json.dumps({'error': 'groq package is not installed'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    client = AsyncGroq(api_key=GROQ_API_KEY)
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=_build_messages(req),
            temperature=0.7,
            max_tokens=512,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'text': content})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception:
        logger.exception("GROQ stream error")
        yield f"data: {json.dumps({'error': 'An internal error occurred.'})}\n\n"
        yield "data: [DONE]\n\n"
