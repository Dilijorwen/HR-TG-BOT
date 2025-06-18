import json, pathlib, yaml
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Contact, ReplyKeyboardRemove
from asyncpg import Pool

from .states import RecruitFlow
from .keyboards import ask_phone_kb # оставить из вашего файла

SCENARIOS = yaml.safe_load(
    pathlib.Path(__file__).with_name("scenarios.yml").read_text(encoding="utf-8")
)

def register_handlers(dp, db_pool: Pool):
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
        vacancy_code = command.args
        script = SCENARIOS.get(vacancy_code)

        if not script:
            await message.answer(
                "⚠️ Cсылка выглядит некорректной. "
                "Попросите HR прислать актуальный линк."
            )
            return

    async def ask_next(message: Message, state: FSMContext, script: dict):
        data = await state.get_data()
        q_index = data["q_index"]
        questions = script["questions"]

        if q_index >= len(questions):              # всё собрано
            await save_and_finish(message, state, script)
            return

        q = questions[q_index]
        kb = ask_phone_kb if q.get("keyboard") == "ask_phone" else ReplyKeyboardRemove()
        await message.answer(q["text"], reply_markup=kb)
        await state.set_state(RecruitFlow.asking)

    @router.message(RecruitFlow.asking)
    async def collect(message: Message, state: FSMContext):
        data = await state.get_data()
        vacancy = data["vacancy"]
        script = SCENARIOS[vacancy]
        q_index = data["q_index"]
        questions = script["questions"]

        # сохраняем
        answers = data["answers"]
        answers[questions[q_index]["id"]] = (
            message.contact.phone_number if isinstance(message.contact, Contact) else message.text.strip()
        )

        # готовимся к следующему
        await state.update_data(q_index=q_index + 1, answers=answers)
        await ask_next(message, state, script)

    async def save_and_finish(message: Message, state: FSMContext, script: dict):
        data = await state.get_data()
        await db_pool.execute(
            """
            INSERT INTO candidates (tg_id, vacancy, answers)
            VALUES ($1, $2, $3::jsonb)
            """,
            message.from_user.id,
            data["vacancy"],
            json.dumps(data["answers"]),
        )
        await message.answer("Спасибо! 🎉 Анкета передана рекрутеру.")
        await state.clear()

    dp.include_router(router)
