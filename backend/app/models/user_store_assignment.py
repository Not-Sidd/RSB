from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserStoreAssignment(Base):
    """
    Many-to-many link between Users (Supervisors, and Staff if multi-store)
    and Stores. Admins do NOT get rows here — their access to all stores in
    their organization is computed from organization_id, not stored.
    """

    __tablename__ = "user_store_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "store_id", name="uq_user_store"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="store_assignments")
    store: Mapped["Store"] = relationship(back_populates="user_assignments")
