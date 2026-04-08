"""Database repository for SisDoa - CRUD operations."""

from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from sisdoa.config import DATABASE_URL
from sisdoa.domain.models import Base, DonationItem


class Database:
    """Database connection and session manager.

    This class handles the SQLite connection and provides
    a session factory for database operations.
    """

    def __init__(self, db_url: str = DATABASE_URL) -> None:
        """Initialize database connection.

        Args:
            db_url: SQLAlchemy database URL. Defaults to SQLite file.
        """
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self._create_tables()

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy Session object.
        """
        return self.SessionLocal()


class DonationItemRepository:
    """Repository for DonationItem CRUD operations.

    This class encapsulates all database operations related
    to donation items, keeping the CLI layer free of DB logic.
    """

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: Database instance for connection management.
        """
        self.db = db

    def create(
        self, name: str, quantity: int, expiration_date: date
    ) -> DonationItem:
        """Create a new donation item.

        Args:
            name: Item name.
            quantity: Number of units.
            expiration_date: Item expiration date.

        Returns:
            The newly created DonationItem.
        """
        session = self.db.get_session()
        try:
            item = DonationItem(
                name=name,
                quantity=quantity,
                expiration_date=expiration_date,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

    def get_by_id(self, item_id: int) -> DonationItem | None:
        """Get a donation item by ID.

        Args:
            item_id: The item's primary key.

        Returns:
            DonationItem if found, None otherwise.
        """
        session = self.db.get_session()
        try:
            stmt = select(DonationItem).where(DonationItem.id == item_id)
            return session.execute(stmt).scalar_one_or_none()
        finally:
            session.close()

    def get_all(self) -> list[DonationItem]:
        """Get all donation items.

        Returns:
            List of all DonationItem records.
        """
        session = self.db.get_session()
        try:
            stmt = select(DonationItem).order_by(DonationItem.expiration_date)
            return list(session.execute(stmt).scalars().all())
        finally:
            session.close()

    def get_near_expiration(self, threshold_days: int = 7) -> list[DonationItem]:
        """Get items near their expiration date.

        Args:
            threshold_days: Days to consider as "near expiration".

        Returns:
            List of DonationItem records expiring within threshold.
        """
        session = self.db.get_session()
        try:
            stmt = select(DonationItem).order_by(DonationItem.expiration_date)
            items = session.execute(stmt).scalars().all()
            return [
                item
                for item in items
                if item.days_until_expiration() <= threshold_days
            ]
        finally:
            session.close()

    def update_quantity(self, item_id: int, quantity_delta: int) -> DonationItem | None:
        """Update item quantity (add or remove).

        Args:
            item_id: The item's primary key.
            quantity_delta: Amount to add (positive) or remove (negative).

        Returns:
            Updated DonationItem if successful, None if item not found.

        Raises:
            ValueError: If resulting quantity would be negative.
        """
        session = self.db.get_session()
        try:
            stmt = select(DonationItem).where(DonationItem.id == item_id)
            item = session.execute(stmt).scalar_one_or_none()
            if item is None:
                return None

            new_quantity = item.quantity + quantity_delta
            if new_quantity < 0:
                raise ValueError(
                    f"Insufficient stock: cannot remove {abs(quantity_delta)} units "
                    f"from item with {item.quantity} units"
                )

            item.quantity = new_quantity
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

    def delete(self, item_id: int) -> bool:
        """Delete a donation item.

        Args:
            item_id: The item's primary key.

        Returns:
            True if item was deleted, False if not found.
        """
        session = self.db.get_session()
        try:
            item = self.get_by_id(item_id)
            if item is None:
                return False

            session.delete(item)
            session.commit()
            return True
        finally:
            session.close()

    def get_expired(self) -> list[DonationItem]:
        """Get all expired items.

        Returns:
            List of DonationItem records that have already expired.
        """
        session = self.db.get_session()
        try:
            stmt = select(DonationItem).order_by(DonationItem.expiration_date)
            items = session.execute(stmt).scalars().all()
            return [item for item in items if item.days_until_expiration() < 0]
        finally:
            session.close()
