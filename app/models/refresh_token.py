from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

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
    token = Column(
        String(512),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )    

    # ------------------------
    # Relationships
    # ------------------------
    user = relationship("User", back_populates="refresh_tokens")

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (        
        UniqueConstraint(
            "token",
            name="uq_refresh_tokens_token",
        ),        
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )