from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class PostHistory(Base):
    __tablename__ = "post_histories"

    # ------------------------
    # Columns
    # ------------------------
    id = Column(Integer, primary_key=True)
    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    edited_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ------------------------
    # Relationships
    # ------------------------
    post = relationship("Post", back_populates="histories")

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (
        Index("ix_post_histories_post_id", "post_id"),
        Index("ix_post_histories_edited_at", "edited_at"),
    )
