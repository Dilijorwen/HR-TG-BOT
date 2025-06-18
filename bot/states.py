from aiogram.fsm.state import StatesGroup, State

class RecruitFlow(StatesGroup):
    asking = State()      # задаём вопросы по списку
    done = State()      # анкета собрана