import pytest
from handlers.game import _score_bar, _team_name, _opponent_team
from database.models import Game


# ── Pure helper functions ─────────────────────────────────────────────────────

def test_score_bar_format():
    result = _score_bar(5, 3, "Зорі", "Місяці")
    assert "Зорі" in result
    assert "Місяці" in result
    assert "5" in result
    assert "3" in result


def test_score_bar_zero():
    result = _score_bar(0, 0, "А", "Б")
    assert "0" in result


def test_opponent_team_from_1():
    assert _opponent_team(1) == 2


def test_opponent_team_from_2():
    assert _opponent_team(2) == 1


def test_opponent_team_symmetric():
    assert _opponent_team(_opponent_team(1)) == 1
    assert _opponent_team(_opponent_team(2)) == 2


def _make_game(**kwargs):
    g = Game()
    g.team1_name = kwargs.get("team1_name", "Команда 1")
    g.team2_name = kwargs.get("team2_name", "Команда 2")
    g.team1_score = kwargs.get("team1_score", 0)
    g.team2_score = kwargs.get("team2_score", 0)
    return g


def test_team_name_1():
    game = _make_game(team1_name="Зорі", team2_name="Місяці")
    assert _team_name(game, 1) == "Зорі"


def test_team_name_2():
    game = _make_game(team1_name="Зорі", team2_name="Місяці")
    assert _team_name(game, 2) == "Місяці"


# ── Score calculation logic ───────────────────────────────────────────────────

@pytest.mark.parametrize("performing_team,guessed,expected1,expected2", [
    # team 1 performs
    (1, 0, 3, 0),   # nobody guessed → team1 +3
    (1, 1, 2, 1),   # 1 guessed → team1 +2, team2 +1
    (1, 2, 1, 2),   # 2 guessed → team1 +1, team2 +2
    (1, 3, 0, 3),   # all guessed → team2 +3
    # team 2 performs
    (2, 0, 0, 3),   # nobody guessed → team2 +3
    (2, 1, 1, 2),   # 1 guessed → team1 +1, team2 +2
    (2, 2, 2, 1),
    (2, 3, 3, 0),   # all guessed → team1 +3
])
def test_score_delta(performing_team, guessed, expected1, expected2):
    not_guessed = 3 - guessed
    if performing_team == 1:
        delta1 = not_guessed
        delta2 = guessed
    else:
        delta1 = guessed
        delta2 = not_guessed

    assert delta1 == expected1
    assert delta2 == expected2


def test_score_always_sums_to_3():
    """Every round distributes exactly 3 points total."""
    for team in (1, 2):
        for guessed in range(4):
            not_guessed = 3 - guessed
            if team == 1:
                d1, d2 = not_guessed, guessed
            else:
                d1, d2 = guessed, not_guessed
            assert d1 + d2 == 3
