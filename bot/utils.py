import functools
import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

from dotenv import load_dotenv

import yaml
from aiogram import Bot
from aiogram.types import Message

from bot.states import RecruitFlow, Expect
from bot.nlp.tone_adapter import soften  # смягчитель fixed-фраз

logger = logging.getLogger("hr-bot.utils")

# ---------------------------------------------------------------------------
#   Пути к YAML-сценариям
# ---------------------------------------------------------------------------
load_dotenv()

SCRIPTS_PATH = Path(os.getenv("SCRIPTS_PATH", "scripts")).resolve()
if not SCRIPTS_PATH.exists():
    logger.warning("Scripts dir '%s' not found", SCRIPTS_PATH)


# ---------------------------------------------------------------------------
#   YAML Loader  (+ LRU cache чтобы не читать файл каждый раз)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=32)
def load_yaml(vacancy_id: str) -> Mapping[str, Any] | None:
    path = SCRIPTS_PATH / f"{vacancy_id}.yaml"
    if not path.exists():
        logger.error("Script %s not found", path)
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        return content  # type: ignore[return-value]
    except yaml.YAMLError as exc:
        logger.exception("YAML parse error in %s: %s", path, exc)
        return None


# ---------------------------------------------------------------------------
#   Контекст для LLM (описание + FAQ)
# ---------------------------------------------------------------------------

def build_context(meta: Mapping[str, Any]) -> str:
    ctx = [f"Вакансия: {meta.get('title', '')}"]

    description = meta.get("description")
    if description:
        ctx.append("\nОписание:\n" + description.strip())

    faq = meta.get("faq", [])
    if faq:
        ctx.append("\nFAQ:")
        for item in faq:
            q = item.get("q")
            a = item.get("a")
            if q and a:
                ctx.append(f"\nQ: {q}\nA: {a}")

    return "\n".join(ctx)


# ---------------------------------------------------------------------------
#   Маппинг id шага → State
# ---------------------------------------------------------------------------

STEP_TO_STATE = {
    "ask_name": RecruitFlow.ask_name,
    "ask_experience": RecruitFlow.ask_experience,
    "ask_schedule": RecruitFlow.ask_schedule,
    "free_chat": RecruitFlow.free_chat,
    "finish": RecruitFlow.finish,
}

def get_state(step_id: str):
    return STEP_TO_STATE.get(step_id)


# ---------------------------------------------------------------------------
#   Helper: отправка фиксированного шага с «Tone Adapter»
# ---------------------------------------------------------------------------

async def send_step(chat_id: int, step: Mapping[str, Any], bot: Bot) -> None:
    text_raw: str = step["internal"]
    tone: str | None = step.get("tone")

    # смягчаем и кэшируем
    text_soft = await soften(text_raw, tone or "friendly")

    # простая клавиатура для yes/no
    keyboard = None
    if Expect.from_str(step.get("expect")) == Expect.YES_NO:
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    await bot.send_message(chat_id, text_soft, reply_markup=keyboard)
