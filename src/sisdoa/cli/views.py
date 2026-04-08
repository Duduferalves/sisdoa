"""CLI views - Output formatting for SisDoa."""

from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sisdoa.domain.models import DonationItem

console = Console()


def format_date(d: date) -> str:
    """Format a date for display.

    Args:
        d: Date object to format.

    Returns:
        Formatted date string (DD/MM/YYYY).
    """
    return d.strftime("%d/%m/%Y")


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Success message to display.
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: Error message to display.
    """
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Warning message to display.
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_item_created(item: DonationItem) -> None:
    """Print confirmation of item creation.

    Args:
        item: The newly created DonationItem.
    """
    print_success(
        f"Item registrado: [bold]{item.name}[/bold] "
        f"(Qtd: {item.quantity}, Validade: {format_date(item.expiration_date)})"
    )


def print_item_removed(item: DonationItem, removed_qty: int) -> None:
    """Print confirmation of stock removal.

    Args:
        item: Updated DonationItem.
        removed_qty: Quantity that was removed.
    """
    print_success(
        f"Baixa de {removed_qty} unidades de [bold]{item.name}[/bold]. "
        f"Saldo restante: {item.quantity}"
    )


def print_item_deleted(item_name: str) -> None:
    """Print confirmation of item deletion.

    Args:
        item_name: Name of deleted item.
    """
    print_success(f"Item [bold]{item_name}[/bold] removido do estoque.")


def print_item_not_found(item_id: int) -> None:
    """Print error for item not found.

    Args:
        item_id: ID of item that wasn't found.
    """
    print_error(f"Item com ID {item_id} não encontrado.")


def print_insufficient_stock(current_qty: int, requested_qty: int) -> None:
    """Print error for insufficient stock.

    Args:
        current_qty: Current quantity in stock.
        requested_qty: Quantity requested for removal.
    """
    print_error(
        f"Estoque insuficiente: item possui {current_qty} unidades, "
        f"mas foi solicitado remover {requested_qty}."
    )


def print_empty_inventory() -> None:
    """Print message when inventory is empty."""
    console.print(
        Panel(
            "[yellow]Nenhum item registrado no estoque.[/yellow]\n\n"
            "Use [bold]sisdoa add[/bold] para registrar uma doação.",
            title="Estoque Vazio",
            border_style="yellow",
        )
    )


def print_inventory_table(items: list[DonationItem], expiry_threshold: int = 7) -> None:
    """Print inventory as a formatted table.

    Args:
        items: List of DonationItem records.
        expiry_threshold: Days to consider as near expiration.
    """
    if not items:
        print_empty_inventory()
        return

    table = Table(title="Estoque de Doações", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Nome", style="bold")
    table.add_column("Quantidade", justify="right")
    table.add_column("Validade", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Dias Restantes", justify="right")

    for item in items:
        days_left = item.days_until_expiration()

        # Determine status and styling
        if days_left < 0:
            status = "[red]VENCIDO[/red]"
            days_str = f"[red]{abs(days_left)} dias atrás[/red]"
        elif days_left <= expiry_threshold:
            status = "[yellow]PRÓXIMO DO VENCIMENTO[/yellow]"
            days_str = f"[yellow]{days_left} dias[/yellow]"
        else:
            status = "[green]OK[/green]"
            days_str = f"[green]{days_left} dias[/green]"

        table.add_row(
            str(item.id),
            item.name,
            str(item.quantity),
            format_date(item.expiration_date),
            status,
            days_str,
        )

    console.print(table)

    # Print alerts for near-expiration items
    near_expiry = [i for i in items if 0 <= i.days_until_expiration() <= expiry_threshold]
    expired = [i for i in items if i.days_until_expiration() < 0]

    if expired:
        console.print()
        console.print(
            Panel(
                f"[red][bold]{len(expired)} item(s) VENCIDO(S)[/bold][/red]\n\n"
                + "\n".join(f"  • {i.name} (venceu em {format_date(i.expiration_date)})" for i in expired),
                title="⚠️ ALERTA DE VALIDADE",
                border_style="red",
            )
        )

    if near_expiry and not expired:
        console.print()
        console.print(
            Panel(
                f"[yellow][bold]{len(near_expiry)} item(s) próximo(s) do vencimento[/bold][/yellow]\n\n"
                + "\n".join(
                    f"  • {i.name} (vence em {i.days_until_expiration()} dias - {format_date(i.expiration_date)})"
                    for i in near_expiry
                ),
                title="⚠️ ALERTA DE VALIDADE",
                border_style="yellow",
            )
        )


def print_alerts(items: list[DonationItem], expiry_threshold: int = 7) -> None:
    """Print alerts for expired and near-expiry items.

    Args:
        items: List of DonationItem records.
        expiry_threshold: Days to consider as near expiration.
    """
    expired = [i for i in items if i.days_until_expiration() < 0]
    near_expiry = [i for i in items if 0 <= i.days_until_expiration() <= expiry_threshold]

    if not expired and not near_expiry:
        print_success("Nenhum item próximo do vencimento ou vencido.")
        return

    if expired:
        console.print(
            Panel(
                f"[red][bold]{len(expired)} item(s) VENCIDO(S)[/bold][/red]\n"
                + "\n".join(f"  • {i.name} - {i.quantity} un. (venceu: {format_date(i.expiration_date)})" for i in expired),
                title="🚨 ITENS VENCIDOS",
                border_style="red",
            )
        )

    if near_expiry:
        console.print()
        console.print(
            Panel(
                f"[yellow][bold]{len(near_expiry)} item(s) próximo(s) do vencimento[/bold][/yellow]\n"
                + "\n".join(
                    f"  • {i.name} - {i.quantity} un. (vence em {i.days_until_expiration()} dias)"
                    for i in near_expiry
                ),
                title="⚠️ PRÓXIMO DO VENCIMENTO",
                border_style="yellow",
            )
        )
