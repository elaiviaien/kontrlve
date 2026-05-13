from datetime import datetime
from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    team1_name: Mapped[str] = mapped_column(String, default="Команда 1")
    team2_name: Mapped[str] = mapped_column(String, default="Команда 2")
    team1_score: Mapped[int] = mapped_column(Integer, default=0)
    team2_score: Mapped[int] = mapped_column(Integer, default=0)
    total_rounds: Mapped[int] = mapped_column(Integer, default=6)
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    current_team: Mapped[int] = mapped_column(Integer, default=1)  # 1 or 2
    status: Mapped[str] = mapped_column(String, default="setup")  # setup|active|finished
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    rounds: Mapped[list["Round"]] = relationship("Round", back_populates="game")


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False)
    team: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or 2
    round_type: Mapped[str] = mapped_column(String, nullable=False)
    situation: Mapped[str] = mapped_column(String, nullable=False)
    words: Mapped[list] = mapped_column(JSON, nullable=False)
    guessed_count: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship("Game", back_populates="rounds")
