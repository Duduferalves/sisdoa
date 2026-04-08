"""SisDoa CLI - Main entry point."""

from __future__ import annotations

from datetime import date

import typer
from rich.console import Console

from sisdoa.cli.views import (
    print_alerts,
    print_error,
    print_insufficient_stock,
    print_inventory_table,
    print_item_created,
    print_item_deleted,
    print_item_not_found,
    print_item_removed,
    print_success,
)
from sisdoa.config import EXPIRY_THRESHOLD_DAYS
from sisdoa.repository.database import Database, DonationItemRepository

app = typer.Typer(
    name="sisdoa",
    help="Sistema de Controle de Doações - Gerencie estoque e validade de doações",
    add_completion=False,
)
console = Console()


def get_repository() -> DonationItemRepository:
    """Get a configured repository instance.

    Returns:
        DonationItemRepository with database connection.
    """
    db = Database()
    return DonationItemRepository(db)


@app.command("add")
def add_item(
    name: str = typer.Argument(..., help="Nome do item (ex: 'Arroz 5kg', 'Paracetamol 500mg')"),
    quantity: int = typer.Argument(..., help="Quantidade de unidades"),
    expiration_date: str = typer.Argument(
        ...,
        help="Data de validade no formato DD/MM/AAAA",
    ),
) -> None:
    """Registrar entrada de um item no estoque.

    Exemplo: sisdoa add "Arroz 5kg" 10 15/12/2026
    """
    # Validate quantity
    if quantity < 0:
        print_error("A quantidade deve ser um número positivo.")
        raise typer.Exit(code=1)

    # Parse expiration date
    try:
        day, month, year = map(int, expiration_date.split("/"))
        exp_date = date(year, month, day)
    except ValueError:
        print_error(
            f"Data inválida: '{expiration_date}'. Use o formato DD/MM/AAAA (ex: 15/12/2026)"
        )
        raise typer.Exit(code=1) from None

    # Check if date is in the past
    if exp_date < date.today():
        print_error(f"Data de validade não pode ser passada: {expiration_date} já venceu.")
        raise typer.Exit(code=1)

    repo = get_repository()
    item = repo.create(name=name, quantity=quantity, expiration_date=exp_date)
    print_item_created(item)


@app.command("list")
def list_items(
    alerts_only: bool = typer.Option(
        False,
        "--alerts",
        "-a",
        help="Mostrar apenas itens próximos do vencimento ou vencidos",
    ),
) -> None:
    """Listar todos os itens no estoque.

    Use --alerts para ver apenas itens que precisam de atenção.
    """
    repo = get_repository()

    if alerts_only:
        items = repo.get_all()
        filtered = [i for i in items if i.days_until_expiration() <= EXPIRY_THRESHOLD_DAYS]
        if not filtered:
            print_success("Nenhum item requer atenção no momento.")
            return
        print_inventory_table(filtered, expiry_threshold=EXPIRY_THRESHOLD_DAYS)
    else:
        items = repo.get_all()
        print_inventory_table(items, expiry_threshold=EXPIRY_THRESHOLD_DAYS)


@app.command("alerts")
def show_alerts() -> None:
    """Mostrar alertas de itens próximos do vencimento ou vencidos."""
    repo = get_repository()
    items = repo.get_all()
    print_alerts(items, expiry_threshold=EXPIRY_THRESHOLD_DAYS)


@app.command("remove")
def remove_stock(
    item_id: int = typer.Argument(..., help="ID do item"),
    quantity: int = typer.Argument(..., help="Quantidade a remover"),
) -> None:
    """Dar baixa no estoque (reduzir quantidade).

    Use este comando quando um item for consumido ou doado.

    Exemplo: sisdoa remove 1 5 (remove 5 unidades do item de ID 1)
    """
    if quantity <= 0:
        print_error("A quantidade a remover deve ser positiva.")
        raise typer.Exit(code=1)

    repo = get_repository()
    item = repo.get_by_id(item_id)

    if item is None:
        print_item_not_found(item_id)
        raise typer.Exit(code=1)

    try:
        updated_item = repo.update_quantity(item_id, -quantity)
        if updated_item:
            print_item_removed(updated_item, quantity)
        else:
            print_item_not_found(item_id)
            raise typer.Exit(code=1)
    except ValueError:
        print_insufficient_stock(item.quantity, quantity)
        raise typer.Exit(code=1) from None


@app.command("delete")
def delete_item(
    item_id: int = typer.Argument(..., help="ID do item a remover"),
) -> None:
    """Remover completamente um item do estoque.

    Use este comando para remover registros inseridos por engano.
    Esta ação não pode ser desfeita.

    Exemplo: sisdoa delete 1 (remove o item de ID 1)
    """
    repo = get_repository()
    item = repo.get_by_id(item_id)

    if item is None:
        print_item_not_found(item_id)
        raise typer.Exit(code=1)

    item_name = item.name
    if repo.delete(item_id):
        print_item_deleted(item_name)
    else:
        print_item_not_found(item_id)
        raise typer.Exit(code=1)


@app.command("info")
def show_info(
    item_id: int = typer.Argument(..., help="ID do item"),
) -> None:
    """Mostrar informações detalhadas de um item específico."""
    repo = get_repository()
    item = repo.get_by_id(item_id)

    if item is None:
        print_item_not_found(item_id)
        raise typer.Exit(code=1)

    days_left = item.days_until_expiration()
    near_expiry = item.is_near_expiration(EXPIRY_THRESHOLD_DAYS)

    status = "OK"
    status_style = "green"

    if days_left < 0:
        status = "VENCIDO"
        status_style = "red"
    elif near_expiry:
        status = "PRÓXIMO DO VENCIMENTO"
        status_style = "yellow"

    console.print()
    console.print(f"[bold]ID:[/bold] {item.id}")
    console.print(f"[bold]Nome:[/bold] {item.name}")
    console.print(f"[bold]Quantidade:[/bold] {item.quantity} unidades")
    console.print(f"[bold]Validade:[/bold] {item.expiration_date.strftime('%d/%m/%Y')}")
    console.print(f"[bold]Dias restantes:[/bold] {days_left} dias")
    console.print(f"[bold]Status:[/bold] [{status_style}]{status}[/{status_style}]")
    console.print()


@app.command("version")
def show_version() -> None:
    """Mostrar versão do SisDoa."""
    from sisdoa import __version__

    console.print(f"[bold cyan]SisDoa[/bold cyan] versão [green]{__version__}[/green]")
    console.print()
    console.print("Sistema de Controle de Doações para pequenas ONGs")
    console.print("Gerencie estoque e validade de doações de alimentos e medicamentos")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
