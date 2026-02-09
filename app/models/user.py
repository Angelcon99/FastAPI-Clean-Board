from sqlalchemy import Boolean, Column, Index, Integer, String, Enum as SqlEnum, text
from sqlalchemy.orm import relationship

from app.core.enums import UserRole
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # ------------------------
    # Columns
    # ------------------------
    id = Column(
        Integer,
        primary_key=True
    )
    email = Column(
        String(100),
        nullable=False,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    nickname = Column(
        String(80),
        nullable=False,
    )

    role = Column(
        SqlEnum(UserRole),
        default=UserRole.USER,
        nullable=False,
    )

    is_deleted = Column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        default=False
    )

    # ------------------------
    # Relationships
    # ------------------------
    posts = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    likes = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    bookmarks = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (        
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_nickname", "nickname", unique=True),
        Index("ix_users_is_deleted", "is_deleted"),
    )