from database import engine, Base
import models

# Database creation tool

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
