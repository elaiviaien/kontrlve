from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.crud import SessionLocal, get_active_game, create_game, update_game, create_round, finish_round
from database.models import Game, Round as RoundModel
from services.content import generate_round_content, ROUND_TYPES
from keyboards.game import ready_keyboard, scoring_keyboard, next_round_keyboard, confirm_end_keyboard
from states.game import SetupStates, GameStates

router = Router()

ROUND_TYPE_LABELS = {
    "stories": "Історія",
    "telemarketing": "Телемагазин",
    "sketch": "Скетч",
    "interview": "Інтерв'ю",
}


def _score_bar(score1: int, score2: int, name1: str, name2: str) -> str:
    return f"*{name1}:* {score1}  |  *{name2}:* {score2}"


def _team_name(game, team: int) -> str:
    return game.team1_name if team == 1 else game.team2_name


def _opponent_team(team: int) -> int:
    return 2 if team == 1 else 1


# ── /newgame ────────────────────────────────────────────────────────────────

@router.message(Command("newgame"))
async def cmd_newgame(message: Message, state: FSMContext):
    async with SessionLocal() as session:
        existing = await get_active_game(session, message.from_user.id)
        if existing:
            await update_game(session, existing, status="finished")

    await state.clear()
    await state.set_state(SetupStates.team1_name)
    await message.answer(
        "Нова гра!\n\nВведи назву *першої команди* (або /skip для «Команда 1»):",
        parse_mode="Markdown",
    )


@router.message(SetupStates.team1_name)
async def setup_team1(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else "Команда 1"
    await state.update_data(team1_name=name)
    await state.set_state(SetupStates.team2_name)
    await message.answer(
        f"Чудово, *{name}*!\n\nВведи назву *другої команди* (або /skip для «Команда 2»):",
        parse_mode="Markdown",
    )


@router.message(SetupStates.team2_name)
async def setup_team2(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else "Команда 2"
    await state.update_data(team2_name=name)
    await state.set_state(SetupStates.rounds_count)
    await message.answer(
        f"*{name}* — готово!\n\nСкільки раундів на команду? Введи число (наприклад, 3 або 5):",
        parse_mode="Markdown",
    )


@router.message(SetupStates.rounds_count)
async def setup_rounds(message: Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        if not (1 <= count <= 20):
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Введи число від 1 до 20.")
        return

    data = await state.get_data()
    async with SessionLocal() as session:
        game = await create_game(session, message.from_user.id)
        await update_game(
            session,
            game,
            team1_name=data["team1_name"],
            team2_name=data["team2_name"],
            total_rounds=count * 2,  # total rounds = rounds per team × 2
            status="active",
        )
        game_id = game.id

    await state.clear()
    await state.update_data(game_id=game_id)
    await state.set_state(GameStates.round_ready)
    await _start_round(message, state)


# ── Round logic ──────────────────────────────────────────────────────────────

async def _start_round(message: Message, state: FSMContext):
    data = await state.get_data()
    game_id = data.get("game_id")

    async with SessionLocal() as session:
        game = await session.get(Game, game_id)

        if game.current_round >= game.total_rounds:
            await _show_final(message, game)
            await update_game(session, game, status="finished")
            await state.clear()
            return

        current_team = game.current_team
        team_name = _team_name(game, current_team)

    await message.answer(f"⏳ Генерую завдання для *{team_name}*…", parse_mode="Markdown")

    content = await generate_round_content()

    async with SessionLocal() as session:
        game = await session.get(Game, game_id)
        round_ = await create_round(
            session,
            game_id=game_id,
            team=current_team,
            round_type=content["round_type"],
            situation=content["situation"],
            words=content["words"],
        )
        round_id = round_.id
        round_num = game.current_round + 1
        total = game.total_rounds
        opponent_name = _team_name(game, _opponent_team(current_team))
        team_name = _team_name(game, current_team)

    await state.update_data(round_id=round_id)

    round_label = ROUND_TYPE_LABELS.get(content["round_type"], content["round_type"])
    words_formatted = " · ".join(f"*{w}*" for w in content["words"])

    await message.answer(
        f"📋 Раунд {round_num}/{total} — {round_label}\n"
        f"Хід команди: *{team_name}*\n\n"
        f"🎭 *Ситуація:*\n{content['situation']}\n\n"
        f"🔑 *Три секретних слова:*\n{words_formatted}\n\n"
        f"Покажи це виконавцю. Коли він готовий — натисни «Готово».\n"
        f"Суперник: *{opponent_name}*",
        parse_mode="Markdown",
        reply_markup=ready_keyboard(),
    )


@router.callback_query(F.data == "round:ready", GameStates.round_ready)
async def round_started(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await callback.message.answer(
        "▶️ Виступ розпочато!\n\n"
        "Після завершення виступу натисни — *скільки слів вгадала команда-суперник?*",
        parse_mode="Markdown",
        reply_markup=scoring_keyboard(),
    )
    await state.set_state(GameStates.scoring)


@router.callback_query(F.data == "round:skip", GameStates.round_ready)
async def round_skip(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Генерую нову ситуацію…")
    await callback.message.edit_reply_markup(reply_markup=None)
    await _start_round(callback.message, state)


@router.callback_query(F.data.startswith("score:"), GameStates.scoring)
async def round_scored(callback: CallbackQuery, state: FSMContext):
    guessed = int(callback.data.split(":")[1])
    not_guessed = 3 - guessed

    data = await state.get_data()
    game_id = data["game_id"]
    round_id = data["round_id"]

    async with SessionLocal() as session:
        game = await session.get(Game, game_id)
        round_ = await session.get(RoundModel, round_id)

        await finish_round(session, round_, guessed)

        current_team = game.current_team
        opponent = _opponent_team(current_team)

        if current_team == 1:
            new_score1 = game.team1_score + not_guessed
            new_score2 = game.team2_score + guessed
        else:
            new_score1 = game.team1_score + guessed
            new_score2 = game.team2_score + not_guessed

        next_team = opponent
        new_round = game.current_round + 1
        is_last = new_round >= game.total_rounds

        await update_game(
            session,
            game,
            team1_score=new_score1,
            team2_score=new_score2,
            current_round=new_round,
            current_team=next_team,
        )

        team_name = _team_name(game, current_team)
        opp_name = _team_name(game, opponent)
        t1 = game.team1_name
        t2 = game.team2_name

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    result_lines = [
        f"✅ Раунд завершено!",
        f"",
        f"Вгадано: *{guessed}/3* → +{guessed} очок до *{opp_name}*",
        f"Не вгадано: *{not_guessed}/3* → +{not_guessed} очок до *{team_name}*",
        f"",
        f"Рахунок: {_score_bar(new_score1, new_score2, t1, t2)}",
    ]

    if is_last:
        result_lines.append("\n🏁 Це був останній раунд!")

    await callback.message.answer(
        "\n".join(result_lines),
        parse_mode="Markdown",
        reply_markup=next_round_keyboard(),
    )


@router.callback_query(F.data == "round:next")
async def next_round(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await state.set_state(GameStates.round_ready)
    await _start_round(callback.message, state)


# ── /scores ──────────────────────────────────────────────────────────────────

@router.message(Command("scores"))
async def cmd_scores(message: Message, state: FSMContext):
    async with SessionLocal() as session:
        game = await get_active_game(session, message.from_user.id)
        if not game:
            await message.answer("Немає активної гри. Почни з /newgame")
            return
        await message.answer(
            f"📊 *Рахунок* (раунд {game.current_round}/{game.total_rounds})\n\n"
            + _score_bar(game.team1_score, game.team2_score, game.team1_name, game.team2_name),
            parse_mode="Markdown",
        )


# ── /skip (in setup) ─────────────────────────────────────────────────────────

@router.message(Command("skip"), SetupStates.team1_name)
async def skip_team1(message: Message, state: FSMContext):
    await state.update_data(team1_name="Команда 1")
    await state.set_state(SetupStates.team2_name)
    await message.answer("Назва: *Команда 1*\n\nВведи назву *другої команди*:", parse_mode="Markdown")


@router.message(Command("skip"), SetupStates.team2_name)
async def skip_team2(message: Message, state: FSMContext):
    await state.update_data(team2_name="Команда 2")
    await state.set_state(SetupStates.rounds_count)
    await message.answer("Назва: *Команда 2*\n\nСкільки раундів на команду?", parse_mode="Markdown")


@router.message(Command("skip"), GameStates.round_ready)
async def skip_round(message: Message, state: FSMContext):
    await _start_round(message, state)


# ── /endgame ─────────────────────────────────────────────────────────────────

@router.message(Command("endgame"))
async def cmd_endgame(message: Message):
    await message.answer("Завершити гру достроково?", reply_markup=confirm_end_keyboard())


@router.callback_query(F.data == "game:end")
async def endgame_confirm_prompt(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await callback.message.answer("Завершити гру достроково?", reply_markup=confirm_end_keyboard())


@router.callback_query(F.data == "game:end_confirm")
async def endgame_confirmed(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    async with SessionLocal() as session:
        game = await get_active_game(session, callback.from_user.id)
        if game:
            await _show_final(callback.message, game)
            await update_game(session, game, status="finished")
    await state.clear()


@router.callback_query(F.data == "game:continue")
async def endgame_cancelled(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Продовжуємо!")


# ── /cancel ──────────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Скасовано. Почни знову з /newgame або /start")


# ── Final screen ─────────────────────────────────────────────────────────────

async def _show_final(message: Message, game):
    s1, s2 = game.team1_score, game.team2_score
    t1, t2 = game.team1_name, game.team2_name

    if s1 > s2:
        winner = f"🏆 Перемагає *{t1}*!"
    elif s2 > s1:
        winner = f"🏆 Перемагає *{t2}*!"
    else:
        winner = "🤝 Нічия!"

    await message.answer(
        f"🎉 *Гра завершена!*\n\n"
        f"{_score_bar(s1, s2, t1, t2)}\n\n"
        f"{winner}\n\n"
        f"Нова гра: /newgame",
        parse_mode="Markdown",
    )
