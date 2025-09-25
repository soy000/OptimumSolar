#!/usr/bin/env python3
"""Simple billing program for OptimumSolar.

This command line application lets you manage clients and create invoices for
OptimumSolar's services in Switzerland. Data is stored locally in JSON files and
invoices can be exported as Markdown documents.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from typing import List, Dict, Any

DATA_PATH = Path("data/billing_data.json")
INVOICES_DIR = Path("invoices")
STANDARD_VAT = 0.077  # 7.7% Swiss VAT


@dataclass
class Client:
    """Represents a client company or individual."""

    client_id: int
    name: str
    address: str
    email: str
    phone: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Client":
        return Client(**data)


@dataclass
class ServiceItem:
    description: str
    quantity: float
    unit_price: float

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ServiceItem":
        return ServiceItem(**data)


@dataclass
class Invoice:
    invoice_id: int
    client_id: int
    invoice_date: str
    due_date: str
    services: List[ServiceItem] = field(default_factory=list)
    vat_rate: float = STANDARD_VAT
    notes: str = ""

    @property
    def subtotal(self) -> float:
        return round(sum(item.total for item in self.services), 2)

    @property
    def vat_amount(self) -> float:
        return round(self.subtotal * self.vat_rate, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.vat_amount, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "client_id": self.client_id,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "services": [item.to_dict() for item in self.services],
            "vat_rate": self.vat_rate,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Invoice":
        services = [ServiceItem.from_dict(item) for item in data.pop("services")]
        return Invoice(services=services, **data)


class BillingDatabase:
    """Handles loading and saving billing data from disk."""

    def __init__(self, path: Path = DATA_PATH):
        self.path = path
        self.data = {"clients": [], "invoices": []}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.save()
            return
        with self.path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self.data["clients"] = [Client.from_dict(c) for c in raw.get("clients", [])]
        self.data["invoices"] = [Invoice.from_dict(i) for i in raw.get("invoices", [])]

    def save(self) -> None:
        payload = {
            "clients": [client.to_dict() for client in self.data["clients"]],
            "invoices": [invoice.to_dict() for invoice in self.data["invoices"]],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    # Client operations
    def next_client_id(self) -> int:
        if not self.data["clients"]:
            return 1
        return max(client.client_id for client in self.data["clients"]) + 1

    def add_client(self, client: Client) -> None:
        self.data["clients"].append(client)
        self.save()

    def list_clients(self) -> List[Client]:
        return list(self.data["clients"])

    def get_client(self, client_id: int) -> Client | None:
        for client in self.data["clients"]:
            if client.client_id == client_id:
                return client
        return None

    # Invoice operations
    def next_invoice_id(self) -> int:
        if not self.data["invoices"]:
            return 1
        return max(invoice.invoice_id for invoice in self.data["invoices"]) + 1

    def add_invoice(self, invoice: Invoice) -> None:
        self.data["invoices"].append(invoice)
        self.save()

    def list_invoices(self) -> List[Invoice]:
        return list(self.data["invoices"])


def prompt(text: str) -> str:
    try:
        return input(text)
    except EOFError:
        print()
        return ""


def display_clients(db: BillingDatabase) -> None:
    clients = db.list_clients()
    if not clients:
        print("Aucun client enregistré.")
        return
    print("\nClients enregistrés :")
    for client in clients:
        print(f"[{client.client_id}] {client.name} - {client.email}")
    print()


def create_client(db: BillingDatabase) -> None:
    print("\nCréation d'un nouveau client")
    name = prompt("Nom / Société : ")
    address = prompt("Adresse : ")
    email = prompt("Email : ")
    phone = prompt("Téléphone (optionnel) : ")

    client = Client(
        client_id=db.next_client_id(),
        name=name.strip(),
        address=address.strip(),
        email=email.strip(),
        phone=phone.strip() or None,
    )
    db.add_client(client)
    print(f"Client {client.name} créé avec l'ID {client.client_id}.\n")


def select_client(db: BillingDatabase) -> Client | None:
    display_clients(db)
    if not db.list_clients():
        return None
    while True:
        client_id = prompt("Entrez l'ID du client : ")
        if not client_id:
            return None
        if client_id.isdigit():
            client = db.get_client(int(client_id))
            if client:
                return client
        print("ID invalide, veuillez réessayer ou laisser vide pour annuler.")


def gather_services() -> List[ServiceItem]:
    services: List[ServiceItem] = []
    print("\nAjoutez des prestations (laisser la description vide pour terminer).")
    while True:
        description = prompt("Description de la prestation : ")
        if not description:
            break
        quantity_input = prompt("Quantité (heures, unités, etc.) : ")
        unit_price_input = prompt("Prix unitaire CHF : ")
        try:
            quantity = float(quantity_input.replace(",", "."))
            unit_price = float(unit_price_input.replace(",", "."))
        except ValueError:
            print("Valeurs numériques invalides, veuillez réessayer.")
            continue
        services.append(ServiceItem(description=description, quantity=quantity, unit_price=unit_price))
    return services


def create_invoice(db: BillingDatabase) -> None:
    print("\nCréation d'une facture")
    client = select_client(db)
    if not client:
        print("Création annulée.\n")
        return

    invoice_date = prompt(f"Date de facturation (AAAA-MM-JJ) [{date.today()}] : ") or str(date.today())
    due_date = prompt("Date d'échéance (AAAA-MM-JJ) : ") or invoice_date

    services = gather_services()
    if not services:
        print("Aucune prestation ajoutée, création de facture annulée.\n")
        return

    vat_input = prompt(f"Taux de TVA (par défaut {STANDARD_VAT * 100:.1f}%): ")
    vat_rate = STANDARD_VAT
    if vat_input:
        try:
            vat_rate = float(vat_input.replace(",", ".")) / 100
        except ValueError:
            print("Taux de TVA invalide, utilisation du taux standard.")

    notes = prompt("Notes (ex: numéro de contrat, modalités de paiement) : ")

    invoice = Invoice(
        invoice_id=db.next_invoice_id(),
        client_id=client.client_id,
        invoice_date=invoice_date,
        due_date=due_date,
        services=services,
        vat_rate=vat_rate,
        notes=notes,
    )
    db.add_invoice(invoice)
    export_invoice(invoice, client)
    print(f"Facture #{invoice.invoice_id} créée pour {client.name}.\n")


def export_invoice(invoice: Invoice, client: Client) -> Path:
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    filename = INVOICES_DIR / f"facture_{invoice.invoice_id}.md"
    lines = [
        f"# Facture OptimumSolar #{invoice.invoice_id}",
        "",
        f"Date de facturation : {invoice.invoice_date}",
        f"Date d'échéance : {invoice.due_date}",
        "",
        "## Client",
        f"**{client.name}**",
        client.address,
        f"Email : {client.email}",
    ]
    if client.phone:
        lines.append(f"Téléphone : {client.phone}")
    lines.extend(
        [
            "",
            "## Prestations",
            "| Description | Quantité | Prix unitaire (CHF) | Total (CHF) |",
            "|-------------|----------|---------------------|-------------|",
        ]
    )
    for service in invoice.services:
        lines.append(
            f"| {service.description} | {service.quantity:g} | {service.unit_price:.2f} | {service.total:.2f} |"
        )
    lines.extend(
        [
            "",
            f"Sous-total : {invoice.subtotal:.2f} CHF",
            f"TVA ({invoice.vat_rate * 100:.1f} %) : {invoice.vat_amount:.2f} CHF",
            f"Total TTC : {invoice.total:.2f} CHF",
        ]
    )
    if invoice.notes:
        lines.extend(["", "## Notes", invoice.notes])

    with filename.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return filename


def list_invoices(db: BillingDatabase) -> None:
    invoices = db.list_invoices()
    if not invoices:
        print("Aucune facture enregistrée.")
        return
    print("\nFactures enregistrées :")
    for invoice in invoices:
        client = db.get_client(invoice.client_id)
        client_name = client.name if client else "Client inconnu"
        print(
            f"Facture #{invoice.invoice_id} - {client_name} - Date : {invoice.invoice_date} - Total : {invoice.total:.2f} CHF"
        )
    print()


def main() -> None:
    db = BillingDatabase()
    actions = {
        "1": ("Lister les clients", display_clients),
        "2": ("Ajouter un client", create_client),
        "3": ("Créer une facture", create_invoice),
        "4": ("Lister les factures", list_invoices),
        "0": ("Quitter", None),
    }

    print("Bienvenue dans le programme de facturation OptimumSolar")
    while True:
        print("\nMenu :")
        for key, (label, _) in actions.items():
            print(f" {key}. {label}")
        choice = prompt("Votre choix : ")
        if choice == "0":
            print("Au revoir !")
            break
        action = actions.get(choice)
        if action:
            _, func = action
            if func:
                func(db)
        else:
            print("Choix invalide, merci de réessayer.")


if __name__ == "__main__":
    main()
