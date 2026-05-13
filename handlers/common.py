from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вітаю! Це бот для гри *КОНТРЛВЕ* за правилами шоу Женя Яновича.\n\n"
        "Механіка:\n"
        "— Виконавець отримує ситуацію та 3 секретних слова\n"
        "— Розповідає монолог, непомітно вплітаючи слова\n"
        "— Суперники намагаються вгадати слова\n\n"
        "Команди:\n"
        "/newgame — нова гра\n"
        "/scores — поточний рахунок\n"
        "/skip — пропустити раунд\n"
        "/endgame — завершити гру\n"
        "/cancel — скасувати дію",
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "*Команди бота:*\n\n"
        "/newgame — почати нову гру\n"
        "/scores — рахунок поточної гри\n"
        "/skip — пропустити поточний раунд\n"
        "/endgame — завершити гру\n"
        "/cancel — скасувати введення\n\n"
        "*Як грати:*\n"
        "1. /newgame → введи назви команд\n"
        "2. Бот показує ситуацію і 3 слова\n"
        "3. Виконавець розповідає монолог IRL\n"
        "4. Після виступу — введи скільки слів вгадала команда-суперник (0-3)\n"
        "5. Черги чергуються, в кінці — переможець",
        parse_mode="Markdown",
    )
