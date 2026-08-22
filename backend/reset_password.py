from database import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(
        text("ALTER ROLE postgres WITH PASSWORD '987654321'")
    )

print("Password changed successfully")