import argparse
import asyncio
from pathlib import Path
from typing import Optional

from encryption import decrypt_metadata
from database import SessionLocal
from init_db import init_db
from inventory_service import save_inventory
import models
from parser import parse_file
from validator import validate_inventory


class LocalUpload:
    def __init__(self, path: Path):
        self.filename = path.name
        self.path = path

    async def read(self) -> bytes:
        return self.path.read_bytes()


def upload_inventory(file_path: Path) -> int:
    if not file_path.is_file():
        raise FileNotFoundError(f"Inventory file not found: {file_path}")

    init_db()
    parsed_df = asyncio.run(parse_file(LocalUpload(file_path)))
    clean_df = validate_inventory(parsed_df)

    with SessionLocal.begin() as db:
        save_inventory(clean_df, db)

    return len(clean_df)


def view_inventory() -> int:
    init_db()
    with SessionLocal() as db:
        items = (
            db.query(models.InventoryItem)
            .order_by(models.InventoryItem.id)
            .all()
        )
        for item in items:
            metadata = decrypt_metadata(item.encrypted_metadata) or {}
            print(
                f"{item.item_name}: {item.quantity:g} {item.unit}; "
                f"expires {item.expiration_date}; "
                f"lot {metadata.get('lot_number', 'n/a')}; "
                f"location {metadata.get('location', 'n/a')}"
            )
        return len(items)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage inventory using the application database and encryption."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser(
        "upload", help="Parse, validate, encrypt, and save an inventory file."
    )
    upload_parser.add_argument("file", type=Path, help="Inventory file to upload.")
    subparsers.add_parser("view", help="List inventory and decrypt metadata.")

    args = parser.parse_args(argv)
    if args.command == "upload":
        count = upload_inventory(args.file)
        print(f"Saved {count} inventory rows.")
    else:
        count = view_inventory()
        if count == 0:
            print("Inventory is empty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
