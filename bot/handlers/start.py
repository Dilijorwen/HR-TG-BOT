import logging
from typing import Any, Mapping

from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import RecruitFlow, CandidateData
from bot.utils import load_yaml, send_step, get_state

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start_deeplink(msg: Message, command: CommandObject, state: FSMContext):
    vacancy_id = command.args
    print(vacancy_id)
    if not vacancy_id:
        await msg.answer(
            "⚠️ Я работаю только по персональной ссылке.\n"
            "Похоже, вы запустили меня напрямую. Попросите HR прислать правильную ссылку."
        )
        return

    script: Mapping[str, Any] | None = load_yaml(vacancy_id)
    if not script:
        await msg.answer("Извините, вакансия не найдена. Сообщите об этом HR.")
        return

    # первый шаг – элемент 0
    first_step: Mapping[str, Any] = script["steps"][0]
    print(script)
    first_state = get_state(first_step["id"])
    if not first_state:
        logger.error("Unknown state id %s in script %s", first_step["id"], vacancy_id)
        await msg.answer("Техническая ошибка сценария. HR уже уведомлён.")
        return

    # сохраняем данные в FSM
    data: CandidateData = {
        "telegram_id": msg.from_user.id,
        "vacancy_id": vacancy_id,
        "questions": [],
    }
    await state.set_state(first_state)
    await state.update_data(script=script, step_index=0, **data)

    # отправляем первый вопрос
    await send_step(msg.chat.id, first_step, msg.bot)
