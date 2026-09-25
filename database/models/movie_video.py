import enum
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class VideoQuality(str, enum.Enum):
    q360 = "360p"
    q480 = "480p"
    q720 = "720p"
    q1080 = "1080p"
    q4k = "4K"


class MovieVideo(Base):
    __tablename__ = "movie_videos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    quality: Mapped[VideoQuality] = mapped_column(Enum(VideoQuality), nullable=False)
    telegram_file_id: Mapped[str] = mapped_column(String(256), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    movie = relationship("Movie", back_populates="videos")
