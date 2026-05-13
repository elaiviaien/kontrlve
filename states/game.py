from aiogram.fsm.state import State, StatesGroup


class SetupStates(StatesGroup):
    team1_name = State()
    team2_name = State()
    rounds_count = State()


class GameStates(StatesGroup):
    round_ready = State()   # content generated, waiting for "Ready" press
    scoring = State()       # waiting for guessed count (0-3)
