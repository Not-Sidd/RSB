import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    STAFF = "staff"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="users")
    store_assignments: Mapped[list["UserStoreAssignment"]] = relationship(back_populates="user")
    submitted_reports: Mapped[list["DailyReport"]] = relationship(
        back_populates="submitted_by",
        foreign_keys="DailyReport.submitted_by_user_id",
    )
    reviewed_reports: Mapped[list["DailyReport"]] = relationship(
        back_populates="reviewed_by",
        foreign_keys="DailyReport.reviewed_by_user_id",
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
