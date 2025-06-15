from aiogram.fsm.state import StatesGroup, State

class RecruitFlow(StatesGroup):
    vacancy    = State()
    full_name  = State()
    phone      = State()
    experience = State()