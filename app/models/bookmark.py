from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"

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
        nullable=False
    )
    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # ------------------------
    # Relationships
    # ------------------------
    user = relationship("User", back_populates="bookmarks")
    post = relationship("Post", back_populates="bookmarks")

    # ------------------------
    # Constraints & Indexes
    # ------------------------
    __table_args__ = (        
        UniqueConstraint(
            "user_id", 
            "post_id", 
            name="uq_bookmarks_user_post"
        ),        
        Index("idx_bookmarks_user_id", "user_id"),
        Index("idx_bookmarks_post_id", "post_id"),
    )
