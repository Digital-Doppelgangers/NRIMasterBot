from aiogram import F, Router 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from app.llm_client import ask_llama, CreateCharacterPrompt

router = Router()


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
    user_prompt = message.text.strip()
    promptAll="[userprompt] "+user_prompt+CreateCharacterPrompt
    try:
        result = ask_llama(promptAll)
    except Exception as e:
        await message.answer(f"Ошибка при обращении к модели: {e}")
        return
    await message.answer(result)
    await state.clear()