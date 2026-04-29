"""Tests for the CLI layer.

These tests verify CLI commands, argument parsing, and user-facing behavior.
All tests use in-memory SQLite to avoid disk I/O.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sisdoa.cli.main import app
from sisdoa.repository.database import Database, DonationItemRepository


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def cli_repo(in_memory_db_url: str) -> DonationItemRepository:
    """Create repository for CLI tests with isolated DB."""
    db = Database(in_memory_db_url)
    return DonationItemRepository(db)


@pytest.fixture
def in_memory_db_url() -> str:
    """Provide in-memory SQLite URL."""
    return "sqlite:///:memory:"


class TestAddCommand:
    """Tests for the 'add' command."""

    def test_add_item_happy_path(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Happy path: add item with valid data."""
        with (
            patch("sisdoa.cli.main.get_repository", return_value=cli_repo),
            patch(
                "sisdoa.cli.main.OpenFoodFactsGateway.fetch_product_name", return_value="Arroz 5kg"
            ),
        ):
            result = cli_runner.invoke(
                app,
                ["add", "7891010101010", "10", "15/12/2026"],
            )

        assert result.exit_code == 0
        assert "Item registrado" in result.stdout
        assert "Arroz 5kg" in result.stdout

        # Verify item was actually created
        items = cli_repo.get_all()
        assert len(items) == 1
        assert items[0].name == "Arroz 5kg"
        assert items[0].quantity == 10

    def test_add_item_invalid_date_format(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: invalid date format."""
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["add", "7891010101010", "10", "2026-12-15"],  # Wrong format
            )

        assert result.exit_code == 1
        assert "Data inválida" in result.stdout
        assert "DD/MM/AAAA" in result.stdout

    def test_add_item_past_date(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: date in the past."""
        past_date = (date.today() - timedelta(days=30)).strftime("%d/%m/%Y")
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["add", "7891010101010", "10", past_date],
            )

        assert result.exit_code == 1
        assert "já venceu" in result.stdout

    def test_add_item_negative_quantity(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: negative quantity."""
        # Negative numbers are interpreted as options by Typer/Click
        # Use "--" to separate options from arguments
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["add", "7891010101010", "--", "-5", "15/12/2026"],
            )

        # Should fail validation (either Typer parsing or our validation)
        assert result.exit_code != 0

    def test_add_item_zero_quantity(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Edge case: zero quantity (valid for pre-registration)."""
        with (
            patch("sisdoa.cli.main.get_repository", return_value=cli_repo),
            patch(
                "sisdoa.cli.main.OpenFoodFactsGateway.fetch_product_name", return_value="Reserva"
            ),
        ):
            result = cli_runner.invoke(
                app,
                ["add", "7891010101010", "0", "15/12/2026"],
            )

        assert result.exit_code == 0
        assert "Item registrado" in result.stdout


class TestListCommand:
    """Tests for the 'list' command."""

    def test_list_empty_inventory(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Edge case: list empty inventory."""
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Nenhum item registrado" in result.stdout

    def test_list_with_items(self, cli_runner: CliRunner, cli_repo: DonationItemRepository) -> None:
        """Happy path: list items in inventory."""
        cli_repo.create("Arroz 5kg", 10, date.today() + timedelta(days=30))
        cli_repo.create("Feijão 1kg", 5, date.today() + timedelta(days=60))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Arroz 5kg" in result.stdout
        assert "Feijão 1kg" in result.stdout
        assert "Estoque de Doações" in result.stdout

    def test_list_alerts_only_with_alerts(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """List only items near expiration."""
        cli_repo.create("Proximo", 5, date.today() + timedelta(days=3))
        cli_repo.create("Longe", 10, date.today() + timedelta(days=90))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(app, ["list", "--alerts"])

        assert result.exit_code == 0
        assert "Proximo" in result.stdout
        assert "Longe" not in result.stdout

    def test_list_alerts_only_no_alerts(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """No alerts when all items are far from expiration."""
        cli_repo.create("Longe", 10, date.today() + timedelta(days=90))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(app, ["list", "--alerts"])

        assert result.exit_code == 0
        assert "Nenhum item requer atenção" in result.stdout


class TestRemoveCommand:
    """Tests for the 'remove' command."""

    def test_remove_stock_happy_path(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Happy path: remove stock successfully."""
        item = cli_repo.create("Arroz 5kg", 10, date.today() + timedelta(days=30))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["remove", str(item.id), "3"],
            )

        assert result.exit_code == 0
        assert "Baixa de 3 unidades" in result.stdout
        assert "Saldo restante: 7" in result.stdout

        # Verify stock was reduced
        updated = cli_repo.get_by_id(item.id)
        assert updated.quantity == 7

    def test_remove_more_than_available(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: remove more than available stock."""
        item = cli_repo.create("Arroz 5kg", 5, date.today() + timedelta(days=30))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["remove", str(item.id), "10"],
            )

        assert result.exit_code == 1
        assert "Estoque insuficiente" in result.stdout

        # Verify stock wasn't changed
        unchanged = cli_repo.get_by_id(item.id)
        assert unchanged.quantity == 5

    def test_remove_nonexistent_item(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: remove from non-existent item."""
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["remove", "9999", "5"],
            )

        assert result.exit_code == 1
        assert "não encontrado" in result.stdout

    def test_remove_zero_quantity(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: remove zero quantity."""
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["remove", "1", "0"],
            )

        assert result.exit_code == 1
        assert "quantidade a remover deve ser positiva" in result.stdout


class TestDeleteCommand:
    """Tests for the 'delete' command."""

    def test_delete_item_happy_path(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Happy path: delete existing item."""
        item = cli_repo.create("Para Deletar", 5, date.today() + timedelta(days=30))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["delete", str(item.id)],
            )

        assert result.exit_code == 0
        assert "removido do estoque" in result.stdout

        # Verify item was deleted
        deleted = cli_repo.get_by_id(item.id)
        assert deleted is None

    def test_delete_nonexistent_item(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: delete non-existent item."""
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["delete", "9999"],
            )

        assert result.exit_code == 1
        assert "não encontrado" in result.stdout


class TestInfoCommand:
    """Tests for the 'info' command."""

    def test_info_success(self, cli_runner: CliRunner, cli_repo: DonationItemRepository) -> None:
        """Happy path: show item info."""
        item = cli_repo.create("Arroz 5kg", 10, date.today() + timedelta(days=30))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["info", str(item.id)],
            )

        assert result.exit_code == 0
        assert "Arroz 5kg" in result.stdout
        assert "10 unidades" in result.stdout
        assert "Status:" in result.stdout

    def test_info_nonexistent(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Failure case: info for non-existent item."""
        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(
                app,
                ["info", "9999"],
            )

        assert result.exit_code == 1
        assert "não encontrado" in result.stdout


class TestAlertsCommand:
    """Tests for the 'alerts' command."""

    def test_alerts_with_expired_and_near(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """Show alerts for expired and near-expiry items."""
        cli_repo.create("Vencido", 5, date.today() - timedelta(days=5))
        cli_repo.create("Proximo", 3, date.today() + timedelta(days=2))
        cli_repo.create("Longe", 10, date.today() + timedelta(days=90))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(app, ["alerts"])

        assert result.exit_code == 0
        assert "VENCIDO" in result.stdout or "Vencido" in result.stdout
        assert "PRÓXIMO" in result.stdout or "Proximo" in result.stdout

    def test_alerts_no_issues(
        self, cli_runner: CliRunner, cli_repo: DonationItemRepository
    ) -> None:
        """No alerts when all items are OK."""
        cli_repo.create("OK", 10, date.today() + timedelta(days=90))

        with patch("sisdoa.cli.main.get_repository", return_value=cli_repo):
            result = cli_runner.invoke(app, ["alerts"])

        assert result.exit_code == 0
        assert "Nenhum item próximo" in result.stdout


class TestVersionCommand:
    """Tests for the 'version' command."""

    def test_version_success(self, cli_runner: CliRunner) -> None:
        """Version command shows version info."""
        result = cli_runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "SisDoa" in result.stdout
        assert "1.0.0" in result.stdout


class TestHelpCommand:
    """Tests for help functionality."""

    def test_help_main(self, cli_runner: CliRunner) -> None:
        """Main help shows available commands."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "list" in result.stdout
        assert "remove" in result.stdout
        assert "delete" in result.stdout
        assert "alerts" in result.stdout

    def test_help_add_command(self, cli_runner: CliRunner) -> None:
        """Help for add command shows usage."""
        result = cli_runner.invoke(app, ["add", "--help"])

        assert result.exit_code == 0
        assert "Código de barras (EAN) do produto" in result.stdout
        assert "Quantidade" in result.stdout
        assert "Data de validade" in result.stdout
