import enum

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ReportStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class DailyReport(Base, TimestampMixin):
    __tablename__ = "daily_reports"
    __table_args__ = (
        UniqueConstraint(
            "store_id", "submitted_by_user_id", "report_date",
            name="uq_report_store_user_date",
        ),
        Index("ix_daily_reports_store_date", "store_id", "report_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False)
    submitted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    report_date: Mapped[Date] = mapped_column(Date, nullable=False)

    total_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    transaction_count: Mapped[int] = mapped_column(default=0, nullable=False)
    cash_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    card_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    other_payment_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    expenses: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    refunds: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.SUBMITTED, nullable=False
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    review_comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    store: Mapped["Store"] = relationship(back_populates="daily_reports")
    submitted_by: Mapped["User"] = relationship(
        back_populates="submitted_reports", foreign_keys=[submitted_by_user_id]
    )
    reviewed_by: Mapped["User | None"] = relationship(
        back_populates="reviewed_reports", foreign_keys=[reviewed_by_user_id]
    )
