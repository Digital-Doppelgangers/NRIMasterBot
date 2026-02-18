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
    userGavePrompt = State()

class CreateCampaignStates(StatesGroup):
    userGaveCampaignName = State()
    userGaveCampaignDescription = State()
@router.message(CommandStart())
async def cmd_start (message: Message):
    await message.answer(
        "Привет!\nЭтот бот создан для помощи мастерам НРИ\n"
        "Доступные команды:\n/campaign_new\n/create_character"
    )

#Создание кампании
@router.message(Command("campaign_new"))
async def cmd_start (message: Message, state: FSMContext):
    await state.set_state(CreateCampaignStates.userGaveCampaignName)
    await message.answer("Напишите название кампании")

@router.message(CreateCampaignStates.userGaveCampaignName)
async def accept_company_name(message: Message, state: FSMContext):
    userCampaignName=message.text.strip()
    await state.update_data(campaign_name=userCampaignName)
    await state.set_state(CreateCampaignStates.userGaveCampaignDescription)
    await message.answer("Краткое описание вашей кампании")

@router.message(CreateCampaignStates.userGaveCampaignDescription)
async def accept_company_Description(message: Message, state: FSMContext):
    userCampaignDescription=message.text.strip()
    await state.update_data(campaign_description=userCampaignDescription)
    data = await state.get_data()
    await message.answer("Кампания успешно создана✅\n"
    f"Название: {data["campaign_name"]}\n"
    f"Описание: {data["campaign_description"]}")
    await state.clear()
    
#Создание персонажа    
@router.message(Command('create_character'))
async def create_character(message: Message, state: FSMContext):
    await state.set_state(CreatecharacterStates.userGavePrompt)
    await message.answer("Напиши, каким ты хочешь видеть персонажа — раса, класс, характер, способность, бэкграунд…")

@router.message(CreatecharacterStates.userGavePrompt)
async def accept_character(message: Message, state: FSMContext):
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