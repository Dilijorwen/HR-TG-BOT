from aiogram.fsm.state import State, StatesGroup
from enum import Enum
from typing import TypedDict, Any


class RecruitFlow(StatesGroup):

    # фиксированные шаги
    ask_name: State = State()
    ask_experience: State = State()
    ask_schedule: State = State()

    # свободный диалог (Q&A)
    free_chat: State = State()

    # завершение
    finish: State = State()


class CandidateData(TypedDict, total=False):
    telegram_id: int
    vacancy_id: str

    # поля анкеты
    full_name: str
    experience: str
    schedule_pref: str

    # накопленный массив вопросов кандидата
    questions: list[str]

    # контекст LLM-сессии для free_chat
    llm_ctx: list[dict[str, Any]]



class Expect(Enum):
    YES_NO = "yes_no"  # да/нет
    FREE_CHAT = "free_chat"  # произвольный текст множ. шагов
    TEXT = "text"  # одиночная текстовая строка

    @classmethod
    def from_str(cls, raw: str | None) -> "Expect | None":
        if raw is None:
            return None
        try:
            return cls(raw)
        except ValueError:
            return None
