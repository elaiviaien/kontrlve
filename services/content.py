import json
import random
from pathlib import Path
from services.llm import ask_haiku

ROUND_TYPES = {
    "stories": "Розкажи особисту або вигадану кумедну історію",
    "telemarketing": "Прорекламуй вигаданий товар у стилі телемагазину",
    "sketch": "Зіграй міні-скетч у ролі персонажа в смішній ситуації",
    "interview": "Відповідай на запитання журналіста як відома людина",
}

SYSTEM_PROMPT = """Ти — асистент для гри КОНТРЛВЕ. Твоя задача — генерувати цікавий контент для раундів.
Відповідай ТІЛЬКИ валідним JSON без жодних пояснень або markdown-блоків."""

_fallback: dict | None = None


def _load_fallback() -> dict:
    global _fallback
    if _fallback is None:
        path = Path(__file__).parent.parent / "data" / "fallback.json"
        _fallback = json.loads(path.read_text(encoding="utf-8"))
    return _fallback


def _get_fallback_content(round_type: str) -> dict:
    data = _load_fallback()
    situations = data["situations"].get(round_type, data["situations"]["stories"])
    situation = random.choice(situations)
    words = random.sample(data["words"], 3)
    return {"round_type": round_type, "situation": situation, "words": words}


async def generate_round_content(round_type: str | None = None) -> dict:
    if round_type is None:
        round_type = random.choice(list(ROUND_TYPES.keys()))

    task_description = ROUND_TYPES[round_type]

    user_prompt = f"""Згенеруй контент для раунду типу "{round_type}".
Завдання для виконавця: {task_description}

Поверни JSON з такими полями:
- "round_type": "{round_type}"
- "situation": конкретна кумедна ситуація для виконавця (1-2 речення, українською)
- "words": масив з 3 секретних слів (українською)

Вимоги до слів:
- Рідковживані, але зрозумілі українські слова
- Різних частин мови: іменник + дієслово + прикметник або прислівник
- НЕ прості побутові слова (не "стіл", "кіт", "вода", "хліб")
- Слова, які можна непомітно вплести в будь-яку розмову
- Приклади хороших слів: "горщик", "честолюбство", "мерехтіти", "запопадливий", "примхливо"

Приклад відповіді:
{{"round_type": "sketch", "situation": "Ти — перукар, який стриже клієнта вперше в житті і намагається не показати паніку", "words": ["горщик", "честолюбство", "мерехтіти"]}}"""

    try:
        raw = await ask_haiku(SYSTEM_PROMPT, user_prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        if not all(k in data for k in ("round_type", "situation", "words")):
            raise ValueError("Missing keys in response")
        if len(data["words"]) != 3:
            raise ValueError("Expected exactly 3 words")
        return data
    except Exception:
        return _get_fallback_content(round_type)
