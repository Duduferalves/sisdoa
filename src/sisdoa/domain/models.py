"""Domain models for SisDoa."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, declarative_base

Base = declarative_base()


class DonationItem(Base):
    """Entity representing a donation item in inventory.

    Attributes:
        id: Primary key, auto-increment.
        name: Name of the donated item (e.g., "Arroz 5kg", "Paracetamol").
        quantity: Number of units in stock (must be >= 0).
        expiration_date: Date when the item expires.
        created_at: Timestamp when the item was registered.
    """

    __tablename__ = "donation_items"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(255), nullable=False)
    quantity: Mapped[int] = Column(Integer, nullable=False, default=0)
    expiration_date: Mapped[date] = Column(Date, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),  # noqa: UP017
    )

    def __repr__(self) -> str:
        return f"<DonationItem(id={self.id}, name='{self.name}', qty={self.quantity})>"

    def is_near_expiration(self, threshold_days: int = 7) -> bool:
        """Check if item is near expiration date.

        Args:
            threshold_days: Number of days to consider as "near expiration".

        Returns:
            True if item expires within threshold_days, False otherwise.
        """
        today = date.today()
        days_until_expiry = (self.expiration_date - today).days
        return days_until_expiry <= threshold_days

    def days_until_expiration(self) -> int:
        """Calculate days remaining until expiration.

        Returns:
            Number of days until expiration. Negative if already expired.
        """
        return (self.expiration_date - date.today()).days
