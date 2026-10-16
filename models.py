from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Current inventroy
class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True)
    quantity = Column(Float)
    unit = Column(String)
    expiration_date = Column(DateTime)
    encrypted_metadata = Column(LargeBinary, nullable=True)

    versions = relationship("InventoryVersion", back_populates="item")

# Full version history
class InventoryVersion(Base):
    __tablename__ = "inventory_versions"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"))
    quantity = Column(Float)
    expiration_date = Column(DateTime)
    timestamp = Column(DateTime, default=datetime.utcnow)

    item = relationship("InventoryItem", back_populates="versions")
