import pytest
from database.models import Game, Round
from database.crud import (
    create_game,
    get_active_game,
    update_game,
    create_round,
    get_last_round,
    finish_round,
)


async def test_create_game(session):
    game = await create_game(session, user_id=42)
    assert game.id is not None
    assert game.user_id == 42
    assert game.status == "setup"
    assert game.team1_score == 0
    assert game.team2_score == 0
    assert game.current_round == 0
    assert game.current_team == 1


async def test_get_active_game_returns_none_when_absent(session):
    result = await get_active_game(session, user_id=99)
    assert result is None


async def test_get_active_game_returns_active(session):
    game = await create_game(session, user_id=1)
    await update_game(session, game, status="active")

    found = await get_active_game(session, user_id=1)
    assert found is not None
    assert found.id == game.id


async def test_get_active_game_ignores_finished(session):
    game = await create_game(session, user_id=2)
    await update_game(session, game, status="finished")

    result = await get_active_game(session, user_id=2)
    assert result is None


async def test_get_active_game_returns_latest(session):
    g1 = await create_game(session, user_id=3)
    await update_game(session, g1, status="active")
    g2 = await create_game(session, user_id=3)
    await update_game(session, g2, status="active")

    found = await get_active_game(session, user_id=3)
    assert found.id == g2.id


async def test_update_game_fields(session):
    game = await create_game(session, user_id=5)
    updated = await update_game(
        session, game,
        team1_name="Зорі",
        team2_name="Місяці",
        total_rounds=6,
        status="active",
    )
    assert updated.team1_name == "Зорі"
    assert updated.team2_name == "Місяці"
    assert updated.total_rounds == 6
    assert updated.status == "active"


async def test_create_round(session):
    game = await create_game(session, user_id=6)
    round_ = await create_round(
        session,
        game_id=game.id,
        team=1,
        round_type="stories",
        situation="Ти застряг у ліфті",
        words=["горщик", "честолюбство", "мерехтіти"],
    )
    assert round_.id is not None
    assert round_.team == 1
    assert round_.words == ["горщик", "честолюбство", "мерехтіти"]
    assert round_.guessed_count is None


async def test_get_last_round_none_when_absent(session):
    game = await create_game(session, user_id=7)
    result = await get_last_round(session, game.id)
    assert result is None


async def test_get_last_round_returns_latest(session):
    game = await create_game(session, user_id=8)
    r1 = await create_round(session, game.id, 1, "stories", "ситуація 1", ["a", "b", "c"])
    r2 = await create_round(session, game.id, 2, "sketch", "ситуація 2", ["x", "y", "z"])

    last = await get_last_round(session, game.id)
    assert last.id == r2.id


async def test_finish_round(session):
    game = await create_game(session, user_id=9)
    round_ = await create_round(session, game.id, 1, "stories", "ситуація", ["a", "b", "c"])
    assert round_.guessed_count is None

    finished = await finish_round(session, round_, guessed_count=2)
    assert finished.guessed_count == 2


async def test_score_update_team1_performs(session):
    """Team 1 performs, 2 guessed → team2 +2, team1 +1."""
    game = await create_game(session, user_id=10)
    await update_game(session, game, status="active", team1_name="А", team2_name="Б")

    guessed = 2
    not_guessed = 3 - guessed
    updated = await update_game(
        session, game,
        team1_score=game.team1_score + not_guessed,
        team2_score=game.team2_score + guessed,
        current_round=game.current_round + 1,
        current_team=2,
    )
    assert updated.team1_score == 1
    assert updated.team2_score == 2
    assert updated.current_team == 2


async def test_score_update_team2_performs(session):
    """Team 2 performs, 0 guessed → team2 +3, team1 +0."""
    game = await create_game(session, user_id=11)
    await update_game(session, game, status="active", current_team=2)

    guessed = 0
    not_guessed = 3 - guessed
    updated = await update_game(
        session, game,
        team1_score=game.team1_score + guessed,
        team2_score=game.team2_score + not_guessed,
        current_round=1,
        current_team=1,
    )
    assert updated.team1_score == 0
    assert updated.team2_score == 3
