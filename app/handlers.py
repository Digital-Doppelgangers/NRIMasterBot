from aiogram import F, Router 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from app.llm_client import ask_llm
from app.prompts import*

router = Router()
WAIT_MESSAGE_GIF_URL="https://media1.tenor.com/m/OuPsTzfoh6cAAAAd/%D1%82%D0%B0%D0%BA%D0%B8%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC-%D0%B7%D0%B0%D0%BF%D0%B8%D1%88%D0%B5%D0%BC.gif"

class CreatecharacterStates(StatesGroup):
    userPrompt = State()


@router.message(CommandStart())
async def cmd_start (message: Message):
    await message.answer("Привет!\nЭтот бот создан для помощи мастерам НРИ\nДоступные команды:\n/create_character")


@router.message(Command('create_character'))
async def create_character(message: Message, state: FSMContext):
    await state.set_state(CreatecharacterStates.userPrompt)
    await message.answer("Напиши, каким ты хочешь видеть персонажа — раса, класс, характер, способность, бэкграунд…")

@router.message(CreatecharacterStates.userPrompt)
async def give_character(message: Message, state: FSMContext):
    userPrompt = message.text.strip()
    thinking_msg = await message.answer_animation(animation=WAIT_MESSAGE_GIF_URL,caption="Думаю над персонажем…")
    try:
        result = await ask_llm(userPrompt, CREATE_CHARACTER_PROMPT)
    except Exception as e:
        await message.answer(f"Ошибка при обращении к модели: {e}")
        return
    await thinking_msg.delete()
    await message.answer(result)
    await state.clear()