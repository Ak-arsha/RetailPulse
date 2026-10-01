"""Database Schema Definitions & Engine Factory supporting PostgreSQL & SQLite fallback."""
import os
import hashlib
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Integer,
                        Float, text)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")


def hash_password(password: str) -> str:
    """Generates a secure SHA-256 hash for user passwords."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_engine(url=DB_URL):
    """Factory creating SQLAlchemy engine for PostgreSQL or SQLite."""
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_size=10, max_overflow=20)


def init_db(engine=None):
    """Initializes tables, constraints, indexes, users table, quarantine DLQ, and audit logs."""
    if engine is None:
        engine = get_engine()

    meta = MetaData()

    # Fact Sales (Retail)
    fact_sales = Table(
        'fact_sales', meta,
        Column('order_id', String(50), primary_key=True),
        Column('order_date', String(20), index=True),
        Column('order_month', String(10), index=True),
        Column('order_day', Integer),
        Column('customer_id', String(50), index=True),
        Column('product_id', String(50), index=True),
        Column('quantity', Integer),
        Column('unit_price', Float),
        Column('discount', Float),
        Column('revenue', Float),
        Column('created_at', String(30))
    )

    # Dim Customer
    dim_customer = Table(
        'dim_customer', meta,
        Column('customer_id', String(50), primary_key=True),
        Column('region', String(50)),
        Column('city', String(50)),
        Column('valid_from', String(30)),
        Column('valid_to', String(30)),
        Column('is_current', Integer)
    )

    # Dim Product
    dim_product = Table(
        'dim_product', meta,
        Column('product_id', String(50), primary_key=True),
        Column('product_name', String(100)),
        Column('category', String(50), index=True)
    )

    # Fact SaaS
    fact_saas = Table(
        'fact_saas_subscriptions', meta,
        Column('customer_id', String(50), primary_key=True),
        Column('tier', String(50), index=True),
        Column('mrr', Float),
        Column('join_date', String(20)),
        Column('churned', Integer),
        Column('seats', Integer),
        Column('created_at', String(30))
    )

    # Fact Healthcare
    fact_healthcare = Table(
        'fact_healthcare_claims', meta,
        Column('claim_id', String(50), primary_key=True),
        Column('patient_id', String(50), index=True),
        Column('claim_type', String(50), index=True),
        Column('claim_amount', Float),
        Column('processing_hours', Float),
        Column('readmitted', Integer),
        Column('claim_date', String(20)),
        Column('created_at', String(30))
    )

    # Fact Hi-Tech
    fact_hitech = Table(
        'fact_hitech_telemetry', meta,
        Column('log_id', String(50), primary_key=True),
        Column('service_name', String(50), index=True),
        Column('latency_ms', Float),
        Column('compute_cost', Float),
        Column('error_count', Integer),
        Column('log_date', String(20)),
        Column('created_at', String(30))
    )

    # Users Table for RBAC Authentication
    users = Table(
        'users', meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('username', String(50), unique=True, index=True),
        Column('hashed_password', String(128)),
        Column('role', String(20)),  # Admin, Analyst, Viewer
        Column('is_active', Integer, default=1),
        Column('created_at', String(30))
    )

    # Quarantine Dead-Letter Queue (DLQ) Table
    quarantine = Table(
        'quarantine_records', meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('dataset_name', String(50), index=True),
        Column('record_id', String(50)),
        Column('raw_payload', String(1000)),
        Column('rejection_reason', String(250)),
        Column('quarantined_at', String(30))
    )

    # GenAI Query Audit Table
    genai_audit = Table(
        'genai_query_audit', meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_query', String(500)),
        Column('generated_sql', String(1000)),
        Column('user_role', String(20)),
        Column('execution_status', String(20)),
        Column('execution_time_ms', Float),
        Column('queried_at', String(30))
    )

    meta.create_all(engine)

    # Seed Default RBAC Users if empty
    with engine.begin() as con:
        try:
            res = con.execute(text("SELECT COUNT(*) FROM users")).fetchone()
            if res and res[0] == 0:
                demo_users = [
                    ("admin", hash_password("admin123"), "Admin", 1, "2026-10-01 00:00:00"),
                    ("analyst", hash_password("analyst123"), "Analyst", 1, "2026-10-01 00:00:00"),
                    ("viewer", hash_password("viewer123"), "Viewer", 1, "2026-10-01 00:00:00")
                ]
                for u in demo_users:
                    con.execute(
                        text("INSERT INTO users (username, hashed_password, role, is_active, created_at) VALUES (:u, :p, :r, :a, :c)"),
                        {"u": u[0], "p": u[1], "r": u[2], "a": u[3], "c": u[4]}
                    )
                print("[Database Schema] Seeded default RBAC users: admin, analyst, viewer.")
        except Exception as e:
            print(f"[Database Schema] User seed note: {e}")

    print(f"[Database Schema] Initialized tables and constraints on engine: {engine.url}")
    return meta


if __name__ == "__main__":
    init_db()
