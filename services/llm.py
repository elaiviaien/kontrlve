import anthropic
from config import ANTHROPIC_API_KEY, HAIKU_MODEL

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _client


async def ask_haiku(system: str, user: str) -> str:
    client = get_client()
    message = await client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text
