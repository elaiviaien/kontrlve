from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from database.models import Base, Game, Round
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_active_game(session: AsyncSession, user_id: int) -> Game | None:
    result = await session.execute(
        select(Game)
        .where(Game.user_id == user_id, Game.status != "finished")
        .order_by(Game.created_at.desc())
    )
    return result.scalar_one_or_none()


async def create_game(session: AsyncSession, user_id: int) -> Game:
    game = Game(user_id=user_id)
    session.add(game)
    await session.commit()
    await session.refresh(game)
    return game


async def update_game(session: AsyncSession, game: Game, **kwargs) -> Game:
    for key, value in kwargs.items():
        setattr(game, key, value)
    await session.commit()
    await session.refresh(game)
    return game


async def create_round(
    session: AsyncSession,
    game_id: int,
    team: int,
    round_type: str,
    situation: str,
    words: list[str],
) -> Round:
    round_ = Round(
        game_id=game_id,
        team=team,
        round_type=round_type,
        situation=situation,
        words=words,
    )
    session.add(round_)
    await session.commit()
    await session.refresh(round_)
    return round_


async def get_last_round(session: AsyncSession, game_id: int) -> Round | None:
    result = await session.execute(
        select(Round)
        .where(Round.game_id == game_id)
        .order_by(Round.id.desc())
    )
    return result.scalars().first()


async def finish_round(session: AsyncSession, round_: Round, guessed_count: int) -> Round:
    round_.guessed_count = guessed_count
    await session.commit()
    await session.refresh(round_)
    return round_
