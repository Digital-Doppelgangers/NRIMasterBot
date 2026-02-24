from aiogram import F, Router 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.types import CallbackQuery

from app.keyboards.compaignKB import*
from app.repos.memory_campaign_repo import*
from app.llm_client import ask_llm
from app.prompts import*

router = Router()
campaign_repo = InMemoryCampaignRepo()

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
        "Доступные команды:\n/campaign_new\n/create_character\n/campaign_list\n/campaign_current"
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
    await campaign_repo.create(message.from_user.id, data["campaign_name"], data["campaign_description"])
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

#Список кампаний

@router.message(Command("campaign_list"))
async def cmd_campaign_list(message: Message):
    campaigns = await campaign_repo.list(user_id=message.from_user.id)

    if not campaigns:
        await message.answer("У тебя пока нет кампаний. Создай: /campaign_new")
        return

    kb = campaign_list_kb(campaigns, page=0, page_size=6)
    await message.answer("Выбери кампанию:", reply_markup=kb)


@router.callback_query(CampaignListCB.filter())
async def cb_campaign_page(call: CallbackQuery, callback_data: CampaignListCB):
    campaigns = await campaign_repo.list(user_id=call.from_user.id)

    if not campaigns:
        await call.answer("Кампаний нет", show_alert=False)
        await call.message.edit_text("У тебя пока нет кампаний. Создай: /campaign_new")
        return

    kb = campaign_list_kb(campaigns, page=callback_data.page, page_size=6)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()

@router.callback_query(CampaignSelectCB.filter())
async def cb_campaign_select(call: CallbackQuery, callback_data: CampaignSelectCB):
    await campaign_repo.set_current(user_id=call.from_user.id, campaign_id=callback_data.campaign_id)

    campaign = await campaign_repo.get(user_id=call.from_user.id, campaign_id=callback_data.campaign_id)
    await call.message.edit_text(f"✅ Текущая кампания: *{campaign.title}*", parse_mode="Markdown")
    await call.answer("Выбрано")

@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()

@router.callback_query(F.data == "close")
async def cb_close(call: CallbackQuery):
    await call.message.delete()
    await call.answer()

#Текущая кампания
@router.message(Command("campaign_current"))
async def cmd_campaign_list(message: Message):
    current_campaign = await campaign_repo.get_current(user_id=message.from_user.id)
    if current_campaign == None:
        await message.answer('На данный момент у вас нет выбранной кампании\nВы можете выбрать её использовав команду /campaign_list или создать новую командой /campaign_new')
    else:await message.answer(f'Текущая кампания: {current_campaign.title}\nОписание: {current_campaign.description}')