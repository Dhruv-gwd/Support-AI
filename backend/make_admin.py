#!/usr/bin/env python3
"""Promote a user to admin by email."""
import sys
from app.models.database import SessionLocal, User

def main():
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email: {email}")
            sys.exit(1)
        user.role = "admin"
        db.commit()
        print(f"User '{email}' is now an admin.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
