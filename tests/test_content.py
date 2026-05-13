import json
import pytest
from unittest.mock import AsyncMock, patch

from services.content import generate_round_content, _get_fallback_content, ROUND_TYPES


# ── Fallback ─────────────────────────────────────────────────────────────────

def test_fallback_returns_valid_structure():
    for round_type in ROUND_TYPES:
        result = _get_fallback_content(round_type)
        assert result["round_type"] == round_type
        assert isinstance(result["situation"], str) and len(result["situation"]) > 5
        assert isinstance(result["words"], list) and len(result["words"]) == 3
        assert all(isinstance(w, str) and w for w in result["words"])


def test_fallback_unknown_type_falls_back_to_stories():
    result = _get_fallback_content("unknown_type")
    assert result["round_type"] == "unknown_type"
    assert len(result["words"]) == 3


def test_fallback_words_are_unique():
    for _ in range(10):
        result = _get_fallback_content("stories")
        assert len(set(result["words"])) == 3, "Fallback words must be unique"


# ── Haiku happy path ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_uses_haiku_response():
    payload = {
        "round_type": "sketch",
        "situation": "Ти — перукар, який боїться ножиць",
        "words": ["горщик", "честолюбство", "мерехтіти"],
    }
    with patch("services.content.ask_haiku", new=AsyncMock(return_value=json.dumps(payload))):
        result = await generate_round_content("sketch")

    assert result["round_type"] == "sketch"
    assert result["situation"] == payload["situation"]
    assert result["words"] == payload["words"]


@pytest.mark.asyncio
async def test_generate_strips_markdown_code_block():
    payload = {
        "round_type": "stories",
        "situation": "Ти застряг у ліфті",
        "words": ["a", "b", "c"],
    }
    wrapped = f"```json\n{json.dumps(payload)}\n```"
    with patch("services.content.ask_haiku", new=AsyncMock(return_value=wrapped)):
        result = await generate_round_content("stories")

    assert result["situation"] == payload["situation"]


@pytest.mark.asyncio
async def test_generate_random_type_when_none():
    payload = {
        "round_type": "telemarketing",
        "situation": "Реклама ложки",
        "words": ["x", "y", "z"],
    }
    with patch("services.content.ask_haiku", new=AsyncMock(return_value=json.dumps(payload))):
        result = await generate_round_content(None)

    assert result["round_type"] in ROUND_TYPES
    assert len(result["words"]) == 3


# ── Haiku error paths → fallback ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_falls_back_on_invalid_json():
    with patch("services.content.ask_haiku", new=AsyncMock(return_value="не JSON взагалі")):
        result = await generate_round_content("stories")

    assert result["round_type"] == "stories"
    assert len(result["words"]) == 3


@pytest.mark.asyncio
async def test_generate_falls_back_on_missing_keys():
    with patch("services.content.ask_haiku", new=AsyncMock(return_value='{"round_type": "sketch"}')):
        result = await generate_round_content("sketch")

    assert result["round_type"] == "sketch"
    assert len(result["words"]) == 3


@pytest.mark.asyncio
async def test_generate_falls_back_on_wrong_word_count():
    payload = {"round_type": "stories", "situation": "test", "words": ["тільки", "два"]}
    with patch("services.content.ask_haiku", new=AsyncMock(return_value=json.dumps(payload))):
        result = await generate_round_content("stories")

    assert len(result["words"]) == 3


@pytest.mark.asyncio
async def test_generate_falls_back_on_api_exception():
    with patch("services.content.ask_haiku", new=AsyncMock(side_effect=Exception("API down"))):
        result = await generate_round_content("interview")

    assert result["round_type"] == "interview"
    assert len(result["words"]) == 3
