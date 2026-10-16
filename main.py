from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from encryption import encrypt_metadata
from init_db import init_db
from parser import parse_file
from validator import validate_inventory
from database import SessionLocal
import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root Endpoint
@app.get("/")
def read_root():
    return {"message": "MMA Inventory API is running"}

# UPLOAD + PARSE + VALIDATE + SAVE
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        df = await parse_file(file)
        clean_df = validate_inventory(df)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

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

        # Check if item already exists
        item = db.query(models.InventoryItem).filter_by(item_name=item_name).first()

        if not item:
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

        # Create version entry
        version = models.InventoryVersion(
            item_id=item.id,
            quantity=quantity,
            expiration_date=expiration_date,
        )
        db.add(version)

    db.commit()

    response_df = clean_df.drop(columns=["lot_number", "location"], errors="ignore")
    return {
        "message": "Inventory uploaded and versioned successfully",
        "rows": response_df.values.tolist(),
    }


# ============================================================
# ⭐ PHASE 5 — NEW ENDPOINTS
# ============================================================

# -----------------------------
# GET CURRENT INVENTORY
# -----------------------------
@app.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    items = db.query(models.InventoryItem).all()

    return [
        {
            "id": item.id,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "expiration_date": item.expiration_date,
        }
        for item in items
    ]


# -----------------------------
# GET VERSION HISTORY FOR ONE ITEM
# -----------------------------
@app.get("/versions/{item_id}")
def get_versions(item_id: int, db: Session = Depends(get_db)):
    versions = (
        db.query(models.InventoryVersion)
        .filter_by(item_id=item_id)
        .order_by(models.InventoryVersion.timestamp.desc())
        .all()
    )

    return [
        {
            "version_id": v.id,
            "item_id": v.item_id,
            "quantity": v.quantity,
            "expiration_date": v.expiration_date,
            "timestamp": v.timestamp,
        }
        for v in versions
    ]
