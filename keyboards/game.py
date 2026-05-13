from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def ready_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Готово, починаємо!", callback_data="round:ready")
    builder.button(text="🔄 Інша ситуація", callback_data="round:skip")
    builder.adjust(1)
    return builder.as_markup()


def scoring_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(4):
        builder.button(text=str(i), callback_data=f"score:{i}")
    builder.adjust(4)
    return builder.as_markup()


def next_round_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Наступний раунд", callback_data="round:next")
    builder.button(text="🏁 Завершити гру", callback_data="game:end")
    builder.adjust(1)
    return builder.as_markup()


def confirm_end_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так, завершити", callback_data="game:end_confirm")
    builder.button(text="❌ Продовжити", callback_data="game:continue")
    builder.adjust(2)
    return builder.as_markup()
