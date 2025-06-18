import json
import pathlib
import yaml
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Contact, ReplyKeyboardRemove
from asyncpg import Pool

from .states import RecruitFlow
from .keyboards import ask_phone_kb, remove_kb


SCENARIOS = yaml.safe_load(
    pathlib.Path(__file__).with_name("scenarios.yml").read_text(encoding="utf-8")
)

def register_handlers(dp, db_pool: Pool) -> None:
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
        vacancy_code = command.args
        script = SCENARIOS.get(vacancy_code)

        if not vacancy_code or not script:
            await message.answer(
                "⚠️ Я работаю только по персональной ссылке.\n"
                "Похоже, вы запустили меня напрямую или код вакансии некорректен.\n"
                "Попросите HR прислать правильную ссылку."
            )
            return

        await message.answer(f"""👋 Привет!

Я чат-бот HR-команды. Помогу пройти короткую анкету по вакансии «{vacancy_code}».

Ответы займут 2–3 минуты и сразу попадут к рекрутеру.  
Начнём!"""
                                 )

        # 1) Показываем описание вакансии
        await message.answer(script["intro"], parse_mode="Markdown")

        # 2) Сохраняем начальные данные FSM
        await state.update_data(
            vacancy=vacancy_code,
            answers={},
            q_index=0,
            started_at=datetime.utcnow().isoformat(),
        )

        # 3) Переходим к первому вопросу
        await ask_next_question(message, state, script)

    async def ask_next_question(
        message: Message,
        state: FSMContext,
        script: dict,
    ) -> None:
        data = await state.get_data()
        idx = data["q_index"]
        questions = script["questions"]

        # Все вопросы заданы ➜ сохраняем кандидата и завершаем
        if idx >= len(questions):
            await save_candidate_to_db(message, state, db_pool)
            return

        q = questions[idx]
        kb = ask_phone_kb if q.get("keyboard") == "ask_phone" else remove_kb

        await message.answer(q["text"], reply_markup=kb)
        await state.set_state(RecruitFlow.asking)

    @router.message(RecruitFlow.asking)
    async def collect_answer(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        vacancy = data["vacancy"]
        script = SCENARIOS[vacancy]
        idx = data["q_index"]
        questions = script["questions"]

        # Извлекаем текст/контакт
        answer_text = (
            message.contact.phone_number
            if isinstance(message.contact, Contact)
            else message.text.strip()
        )

        answers = data["answers"]
        answers[questions[idx]["id"]] = answer_text

        # Обновляем FSM и спрашиваем следующий
        await state.update_data(q_index=idx + 1, answers=answers)
        await ask_next_question(message, state, script)

    async def save_candidate_to_db(
        message: Message,
        state: FSMContext,
        pool: Pool,
    ) -> None:
        data = await state.get_data()

        await pool.execute(
            """
            INSERT INTO candidates (tg_id, vacancy, answers)
            VALUES ($1, $2, $3::jsonb)
            """,
            message.from_user.id,
            data["vacancy"],
            json.dumps(data["answers"]),
        )

        await message.answer(
            "Спасибо! 🎉 Анкета передана рекрутеру.\n"
            "Мы свяжемся с вами, как только изучим ответы.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

    dp.include_router(router)
