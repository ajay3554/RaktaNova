from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# =========================================================
# DATABASE URL
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./rakta_nova.db"


# =========================================================
# DATABASE ENGINE
# =========================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# =========================================================
# SESSION
# =========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# =========================================================
# BASE
# =========================================================

Base = declarative_base()


# =========================================================
# DATABASE MIGRATION
# =========================================================

def migrate_database():

    with engine.connect() as connection:

        # Check whether password column exists
        result = connection.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'donors'
                AND column_name = 'password'
            """)
        )

        password_exists = result.fetchone()

        if not password_exists:

            print("Adding password column to donors table...")

            connection.execute(
                text("""
                    ALTER TABLE donors
                    ADD COLUMN password VARCHAR
                """)
            )

            connection.commit()

            print("Password column added successfully.")

        else:

            print("Password column already exists.")

                # Check whether response column exists
        result = connection.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'notifications'
                AND column_name = 'response'
            """)
        )

        response_exists = result.fetchone()

        if not response_exists:

            print("Adding response column to notifications table...")

            connection.execute(
                text("""
                    ALTER TABLE notifications
                    ADD COLUMN response VARCHAR(20)
                """)
            )

            connection.commit()

            print("response column added successfully.")

        else:

            print("response column already exists.")
                # Check whether request_type column exists
        result = connection.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'blood_requests'
                AND column_name = 'request_type'
            """)
        )

        request_type_exists = result.fetchone()

        if not request_type_exists:

            print("Adding request_type column to blood_requests table...")

            connection.execute(
                text("""
                    ALTER TABLE blood_requests
                    ADD COLUMN request_type VARCHAR(20) DEFAULT 'emergency'
                """)
            )

            connection.commit()

            print("request_type column added successfully.")

        else:

            print("request_type column already exists.")


# =========================================================
# RUN MIGRATION
# =========================================================

try:
    if engine.dialect.name == "postgresql":
        migrate_database()
except Exception as error:
    print("Database migration warning:", error)