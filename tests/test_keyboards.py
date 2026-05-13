from keyboards.game import ready_keyboard, scoring_keyboard, next_round_keyboard, confirm_end_keyboard


def _flat_buttons(markup):
    return [btn for row in markup.inline_keyboard for btn in row]


def test_ready_keyboard_has_two_buttons():
    kb = ready_keyboard()
    buttons = _flat_buttons(kb)
    assert len(buttons) == 2


def test_ready_keyboard_callback_data():
    kb = ready_keyboard()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert "round:ready" in data
    assert "round:skip" in data


def test_scoring_keyboard_has_four_buttons():
    kb = scoring_keyboard()
    buttons = _flat_buttons(kb)
    assert len(buttons) == 4


def test_scoring_keyboard_covers_0_to_3():
    kb = scoring_keyboard()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert data == {"score:0", "score:1", "score:2", "score:3"}


def test_scoring_keyboard_labels_are_digits():
    kb = scoring_keyboard()
    labels = {btn.text for row in kb.inline_keyboard for btn in row}
    assert labels == {"0", "1", "2", "3"}


def test_next_round_keyboard_has_two_buttons():
    kb = next_round_keyboard()
    buttons = _flat_buttons(kb)
    assert len(buttons) == 2


def test_next_round_keyboard_callback_data():
    kb = next_round_keyboard()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert "round:next" in data
    assert "game:end" in data


def test_confirm_end_keyboard_has_two_buttons():
    kb = confirm_end_keyboard()
    buttons = _flat_buttons(kb)
    assert len(buttons) == 2


def test_confirm_end_keyboard_callback_data():
    kb = confirm_end_keyboard()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert "game:end_confirm" in data
    assert "game:continue" in data
