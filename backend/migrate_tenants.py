#!/usr/bin/env python3
"""Migrate existing database to add tenant support."""
import sys
from app.models.database import Base, engine
from sqlalchemy import inspect, text

def main():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("Existing tables:", existing_tables)
    
    if "tenants" not in existing_tables:
        print("Creating tenants table...")
        Base.metadata.create_all(engine, tables=[Base.metadata.tables["tenants"]])
    
    if "documents" not in existing_tables:
        print("Creating documents table...")
        Base.metadata.create_all(engine, tables=[Base.metadata.tables["documents"]])
    
    if "users" in existing_tables:
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "tenant_id" not in columns:
            print("Adding tenant_id column to users...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN tenant_id INTEGER"))
                conn.commit()
    
    print("Migration complete!")
    
    users_without_tenant = engine.execute(text("SELECT id, email FROM users WHERE tenant_id IS NULL")).fetchall()
    if users_without_tenant:
        print(f"Found {len(users_without_tenant)} users without tenant_id. Creating default tenant...")
        with engine.connect() as conn:
            result = conn.execute(text("INSERT INTO tenants (name, slug) VALUES ('Default', 'default')"))
            conn.commit()
            tenant_id = result.lastrowid
            
            for user_id, email in users_without_tenant:
                conn.execute(text("UPDATE users SET tenant_id = :tid WHERE id = :uid"), {"tid": tenant_id, "uid": user_id})
                print(f"  Assigned user {email} (id={user_id}) to tenant {tenant_id}")
            conn.commit()
    
    print("Done!")

if __name__ == "__main__":
    main()
