from sqlalchemy import Column, Index, Integer, String, Text, DateTime, Boolean, ForeignKey, func, text, Enum
from sqlalchemy.orm import relationship

from app.core.enums import PostCategory
from app.db.base import Base


class Post(Base):
    __tablename__ = "posts"

    # ------------------------
    # Columns
    # ------------------------
    id = Column(
        Integer,
        primary_key=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(
        String(100),
        nullable=False
    )
    content = Column(
        Text,
        nullable=False
    )
    category = Column(
        Enum(PostCategory),
        nullable=False
    )
    views = Column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    likes_count = Column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    is_deleted = Column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        default=False,        
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ------------------------
    # Relationships
    # ------------------------
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    histories = relationship("PostHistory", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="post", cascade="all, delete-orphan")

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (
        Index("ix_posts_user_id", "user_id"),
        Index("ix_posts_title", "title"),
        Index("ix_posts_views", "views"),
        Index("ix_posts_likes_count", "likes_count"),
        Index("ix_posts_is_deleted", "is_deleted"),
        Index("ix_posts_created_at", "created_at"),
    )
