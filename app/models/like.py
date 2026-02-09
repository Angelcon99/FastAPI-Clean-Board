from sqlalchemy import Column, Index, Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Like(Base):
    __tablename__ = "likes"

    # ------------------------
    # Columns
    # ------------------------
    id = Column(
        Integer,
        primary_key=True
    )
    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ------------------------
    # Relationships
    # ------------------------
    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (        
        UniqueConstraint(
            "user_id",
            "post_id",
            name="uq_likes_user_post",
        ),        
        Index("ix_likes_user_id", "user_id"),
        Index("ix_likes_post_id", "post_id"),
    )
