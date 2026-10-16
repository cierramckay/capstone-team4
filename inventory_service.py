import pandas as pd
from sqlalchemy.orm import Session

from encryption import encrypt_metadata
import models


def save_inventory(clean_df: pd.DataFrame, db: Session) -> None:
    metadata_columns = [
        column for column in ("lot_number", "location") if column in clean_df.columns
    ]

    for _, row in clean_df.iterrows():
        item_name = row["item_name"]
        quantity = float(row["quantity"])
        unit = row["unit"]
        expiration_date = row["expiration_date"]
        metadata = {
            column: str(row[column]).strip()
            for column in metadata_columns
            if not pd.isna(row[column]) and str(row[column]).strip()
        }
        encrypted_metadata = encrypt_metadata(metadata)

        item = db.query(models.InventoryItem).filter_by(item_name=item_name).first()
        if item is None:
            item = models.InventoryItem(
                item_name=item_name,
                quantity=quantity,
                unit=unit,
                expiration_date=expiration_date,
                encrypted_metadata=encrypted_metadata,
            )
            db.add(item)
            db.flush()
        else:
            item.quantity = quantity
            item.expiration_date = expiration_date
            if metadata_columns:
                item.encrypted_metadata = encrypted_metadata

        db.add(
            models.InventoryVersion(
                item_id=item.id,
                quantity=quantity,
                expiration_date=expiration_date,
            )
        )

    db.commit()
