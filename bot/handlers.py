from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message, Contact
from asyncpg import Pool
from .states import RecruitFlow
from .keyboards import ask_phone_kb, remove_kb

router = Router()

def register_handlers(dp, db: Pool):
    # Подвязываем DB-пул через замыкание
    @router.message(CommandStart())  # фильтр остаётся
    async def cmd_start(
            message: Message,
            command: CommandObject,  # ← объект с разбором /start
            state: FSMContext
    ):
        vacancy_code = command.args  # всё, что после /start

        if not vacancy_code:  # deep-link пустой
            await message.answer(
                "⚠️ Я работаю только по персональной ссылке.\n"
                "Похоже, вы запустили меня напрямую. "
                "Попросите HR прислать правильную ссылку."
            )
            return

        await state.update_data(vacancy=vacancy_code)
        await message.answer("Привет! 👋\nКак Вас зовут?")
        await state.set_state(RecruitFlow.full_name)

    @router.message(RecruitFlow.full_name)
    async def get_name(msg: Message, state: FSMContext):
        await state.update_data(full_name=msg.text.strip())
        await msg.answer("Отправьте пожалуйста номер телефона", reply_markup=ask_phone_kb)
        await state.set_state(RecruitFlow.phone)

    @router.message(RecruitFlow.phone, F.contact)
    async def get_phone(msg: Message, state: FSMContext):
        phone: Contact = msg.contact
        await state.update_data(phone=phone.phone_number)
        await msg.answer("Сколько лет опыта у Вас по профильной работе?", reply_markup=remove_kb)
        await state.set_state(RecruitFlow.experience)

    @router.message(RecruitFlow.experience)
    async def get_exp(msg: Message, state: FSMContext):
        await state.update_data(experience=msg.text.strip())
        data = await state.get_data()
        # минимальная валидация: можно добавить проверки
        await save_candidate(db, msg.from_user.id, **data)
        await msg.answer(
            "Спасибо! 🎉 Ваши данные переданы рекрутеру. "
            "Мы свяжемся с Вами в ближайшее время."
        )
        await state.clear()

    dp.include_router(router)


async def save_candidate(db: Pool, tg_id: int, **data):
    query = """
        INSERT INTO candidates (tg_id, vacancy, full_name, phone, experience)
        VALUES ($1, $2, $3, $4, $5)
    """
    await db.execute(
        query,
        tg_id, data["vacancy"], data["full_name"],
        data["phone"], data["experience"]
    )