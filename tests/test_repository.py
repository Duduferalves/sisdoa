"""Tests for the repository layer.

These tests verify CRUD operations, business logic, and edge cases
for the DonationItemRepository. All tests use in-memory SQLite.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from sisdoa.domain.models import DonationItem
from sisdoa.repository.database import DonationItemRepository


class TestCreateItem:
    """Tests for creating donation items."""

    def test_create_item_success(self, test_repo: DonationItemRepository) -> None:
        """Happy path: create item with valid data."""
        item = test_repo.create(
            name="Arroz 5kg",
            quantity=10,
            expiration_date=date.today() + timedelta(days=30),
        )

        assert item.id is not None
        assert item.name == "Arroz 5kg"
        assert item.quantity == 10
        assert item.expiration_date == date.today() + timedelta(days=30)
        assert item.created_at is not None

    def test_create_item_with_zero_quantity(self, test_repo: DonationItemRepository) -> None:
        """Edge case: create item with zero quantity (valid for pre-registration)."""
        item = test_repo.create(
            name="Reserva Futura",
            quantity=0,
            expiration_date=date.today() + timedelta(days=90),
        )

        assert item.quantity == 0
        assert item.id is not None

    def test_create_item_with_past_expiration(self, test_repo: DonationItemRepository) -> None:
        """Edge case: allow creating expired items (may be needed for inventory audit)."""
        # Repository doesn't validate date - that's a CLI concern
        item = test_repo.create(
            name="Item Vencido",
            quantity=5,
            expiration_date=date.today() - timedelta(days=10),
        )

        assert item is not None
        assert item.days_until_expiration() < 0


class TestReadItems:
    """Tests for reading donation items."""

    def test_get_by_id_success(
        self, sample_item: DonationItem, test_repo: DonationItemRepository
    ) -> None:
        """Happy path: retrieve existing item by ID."""
        item = test_repo.get_by_id(sample_item.id)

        assert item is not None
        assert item.id == sample_item.id
        assert item.name == sample_item.name

    def test_get_by_id_not_found(self, test_repo: DonationItemRepository) -> None:
        """Edge case: retrieve non-existent item."""
        item = test_repo.get_by_id(9999)
        assert item is None

    def test_get_all_empty(self, test_repo: DonationItemRepository) -> None:
        """Edge case: get all items from empty database."""
        items = test_repo.get_all()
        assert items == []

    def test_get_all_with_items(
        self, test_repo: DonationItemRepository, sample_item: DonationItem
    ) -> None:
        """Happy path: get all items with data in database."""
        items = test_repo.get_all()
        assert len(items) >= 1
        assert any(i.id == sample_item.id for i in items)

    def test_get_all_ordered_by_expiration(self, test_repo: DonationItemRepository) -> None:
        """Verify items are ordered by expiration date."""
        # Create items with different expiration dates
        test_repo.create("Item A", 1, date.today() + timedelta(days=100))
        test_repo.create("Item B", 1, date.today() + timedelta(days=10))
        test_repo.create("Item C", 1, date.today() + timedelta(days=50))

        items = test_repo.get_all()

        assert len(items) == 3
        assert items[0].expiration_date <= items[1].expiration_date
        assert items[1].expiration_date <= items[2].expiration_date


class TestGetNearExpiration:
    """Tests for near-expiration queries."""

    def test_get_near_expiration_none(self, test_repo: DonationItemRepository) -> None:
        """All items are far from expiration."""
        test_repo.create("Item Longo", 10, date.today() + timedelta(days=365))
        test_repo.create("Item Medio", 5, date.today() + timedelta(days=30))

        near = test_repo.get_near_expiration(threshold_days=7)
        assert len(near) == 0

    def test_get_near_expiration_some(
        self, test_repo: DonationItemRepository, near_expiry_item: DonationItem
    ) -> None:
        """Some items are near expiration."""
        # near_expiry_item expires in 3 days (fixture)
        test_repo.create("Item Longe", 10, date.today() + timedelta(days=90))

        near = test_repo.get_near_expiration(threshold_days=7)

        assert len(near) == 1
        assert near[0].id == near_expiry_item.id

    def test_get_expired_items(self, test_repo: DonationItemRepository) -> None:
        """Get only expired items."""
        expired = test_repo.create("Vencido", 5, date.today() - timedelta(days=10))
        test_repo.create("Valido", 10, date.today() + timedelta(days=30))

        expired_items = test_repo.get_expired()

        assert len(expired_items) == 1
        assert expired_items[0].id == expired.id


class TestUpdateQuantity:
    """Tests for updating item quantity."""

    def test_remove_quantity_success(
        self, test_repo: DonationItemRepository, sample_item: DonationItem
    ) -> None:
        """Happy path: remove quantity from item."""
        original_qty = sample_item.quantity
        remove_qty = 3

        updated = test_repo.update_quantity(sample_item.id, -remove_qty)

        assert updated is not None
        assert updated.quantity == original_qty - remove_qty

    def test_remove_all_quantity(
        self, test_repo: DonationItemRepository, sample_item: DonationItem
    ) -> None:
        """Edge case: remove all quantity (result in zero)."""
        updated = test_repo.update_quantity(sample_item.id, -sample_item.quantity)

        assert updated is not None
        assert updated.quantity == 0

    def test_remove_more_than_available_raises_error(
        self, test_repo: DonationItemRepository, sample_item: DonationItem
    ) -> None:
        """Failure case: attempt to remove more than available."""
        with pytest.raises(ValueError, match="Insufficient stock"):
            test_repo.update_quantity(sample_item.id, -(sample_item.quantity + 1))

    def test_add_quantity_success(
        self, test_repo: DonationItemRepository, sample_item: DonationItem
    ) -> None:
        """Happy path: add quantity to item (new donation)."""
        original_qty = sample_item.quantity
        add_qty = 5

        updated = test_repo.update_quantity(sample_item.id, add_qty)

        assert updated is not None
        assert updated.quantity == original_qty + add_qty

    def test_update_nonexistent_item(self, test_repo: DonationItemRepository) -> None:
        """Failure case: update quantity of non-existent item."""
        result = test_repo.update_quantity(9999, -5)
        assert result is None


class TestDeleteItem:
    """Tests for deleting items."""

    def test_delete_success(self, test_repo: DonationItemRepository) -> None:
        """Happy path: delete existing item."""
        item = test_repo.create("Para Deletar", 5, date.today() + timedelta(days=30))

        result = test_repo.delete(item.id)

        assert result is True
        assert test_repo.get_by_id(item.id) is None

    def test_delete_nonexistent(self, test_repo: DonationItemRepository) -> None:
        """Failure case: delete non-existent item."""
        result = test_repo.delete(9999)
        assert result is False


class TestDomainLogic:
    """Tests for domain model business logic."""

    def test_is_near_expiration_true(self, test_repo: DonationItemRepository) -> None:
        """Item is near expiration."""
        item = test_repo.create("Proximo", 5, date.today() + timedelta(days=3))
        assert item.is_near_expiration(threshold_days=7) is True

    def test_is_near_expiration_false(self, test_repo: DonationItemRepository) -> None:
        """Item is far from expiration."""
        item = test_repo.create("Longe", 5, date.today() + timedelta(days=60))
        assert item.is_near_expiration(threshold_days=7) is False

    def test_days_until_expiration_positive(self, test_repo: DonationItemRepository) -> None:
        """Calculate days until future expiration."""
        days = 45
        item = test_repo.create("Futuro", 5, date.today() + timedelta(days=days))
        assert item.days_until_expiration() == days

    def test_days_until_expiration_negative(self, test_repo: DonationItemRepository) -> None:
        """Calculate days for already expired item."""
        days_ago = 10
        item = test_repo.create("Vencido", 5, date.today() - timedelta(days=days_ago))
        assert item.days_until_expiration() == -days_ago

    def test_days_until_expiration_today(self, test_repo: DonationItemRepository) -> None:
        """Item expires today (0 days)."""
        item = test_repo.create("Hoje", 5, date.today())
        assert item.days_until_expiration() == 0
