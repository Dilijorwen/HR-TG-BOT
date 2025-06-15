import logging
import os

from dotenv import load_dotenv

import httpx

logger = logging.getLogger(__name__)


load_dotenv()

LLM_URL = os.environ["TG_TOKEN"]
LLM_MODEL = os.environ["TG_TOKEN"]
LLM_TIMEOUT_S = int(os.getenv("LLM_TIMEOUT", "2000000"))




async def soften(text_raw: str, style: str = "friendly") -> str:

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as client:
            r = await client.post(
                LLM_URL,
                json={
                    "model": LLM_MODEL,
                    "prompt": f"Перефразируй: {text_raw.strip()}",
                    "system": f"Ты HR-специалист, отвечай по-русски, {style}, без тегов, до 60 слов.",
                    "stream": False,
                    "options": {"temperature": 0.8},
                },
            )
        r.raise_for_status()
        return r.json().get("response", text_raw).strip()
    except Exception as exc:
        logger.warning("LLM request failed (%s) – returning original text", exc)
        return text_raw.strip()
