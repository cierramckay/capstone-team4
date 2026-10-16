from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session

from parser import parse_file
from validator import validate_inventory
from database import SessionLocal
import models


app = FastAPI()

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
    df = await parse_file(file)
    clean_df = validate_inventory(df)

    for _, row in clean_df.iterrows():
        item_name = row["item_name"]
        quantity = float(row["quantity"])
        unit = row["unit"]
        expiration_date = row["expiration_date"]

        # Check if item already exists
        item = db.query(models.InventoryItem).filter_by(item_name=item_name).first()

        if not item:
            item = models.InventoryItem(
                item_name=item_name,
                quantity=quantity,
                unit=unit,
                expiration_date=expiration_date,
            )
            db.add(item)
            db.flush()
        else:
            item.quantity = quantity
            item.expiration_date = expiration_date

        # Create version entry
        version = models.InventoryVersion(
            item_id=item.id,
            quantity=quantity,
            expiration_date=expiration_date,
        )
        db.add(version)

    db.commit()

    return {
        "message": "Inventory uploaded and versioned successfully",
        "rows": clean_df.values.tolist(),
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
