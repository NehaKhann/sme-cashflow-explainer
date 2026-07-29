import os
import json
import logging
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
DEFAULT_MODEL = os.getenv("CHAT_MODEL", "ledger-chatbot")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    model: str = DEFAULT_MODEL


class ChatMessage(BaseModel):
    role: str
    content: str


@router.post("")
async def chat(req: ChatRequest):
    """
    Proxy a chat message to Ollama and stream the response back.

    Expects Ollama to be running locally with the fine-tuned model loaded:
      ollama run ledger-chatbot

    The request builds a conversation from the provided history + new message,
    sends it to Ollama's /api/chat endpoint, and streams tokens back as SSE.
    """
    ollama_url = f"{OLLAMA_BASE}/api/chat"

    messages = []
    for msg in req.history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": req.message})

    payload = {
        "model": req.model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 512,
        },
    }

    return StreamingResponse(
        _stream_ollama(ollama_url, payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_ollama(url: str, payload: dict) -> AsyncGenerator[str, None]:
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
        except Exception as e:
            logger.exception("Ollama stream error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
