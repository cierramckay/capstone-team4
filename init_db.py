from sqlalchemy import inspect, text

from database import engine, Base
import models

# Database creation tool

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        columns = {
            column["name"]
            for column in inspect(connection).get_columns("inventory_items")
        }
        if "encrypted_metadata" not in columns:
            connection.execute(
                text("ALTER TABLE inventory_items ADD COLUMN encrypted_metadata BLOB")
            )

if __name__ == "__main__":
    init_db()
