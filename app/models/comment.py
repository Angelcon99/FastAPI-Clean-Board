from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, func, text, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

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
        nullable=False
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    parent_id = Column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    content = Column(Text, nullable=False)

    is_deleted = Column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        default=False
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ------------------------
    # Relationships
    # ------------------------
    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (
        Index("ix_comments_post_id", "post_id"),
        Index("ix_comments_user_id", "user_id"),
        Index("ix_comments_parent_id", "parent_id"),
        Index("ix_comments_is_deleted", "is_deleted"),
    )