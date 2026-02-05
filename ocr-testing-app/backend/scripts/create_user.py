#!/usr/bin/env python
"""
CLI script to create users for the Court Form OCR Testing App.

Usage:
    python create_user.py --email user@example.com
    python create_user.py --email user@example.com --password mypassword

If no password is provided, a random secure password will be generated.
"""
import argparse
import asyncio
import secrets
import string
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth.utils import hash_password
from app.services.firestore import FirestoreService


def generate_password(length: int = 16) -> str:
    """Generate a random secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


async def create_user(email: str, password: str) -> None:
    """Create a user in Firestore."""
    firestore = FirestoreService()

    # Check if user already exists
    existing_user = await firestore.get_user_by_email(email)
    if existing_user:
        print(f"Error: User with email '{email}' already exists.")
        sys.exit(1)

    # Hash password and create user
    password_hash = hash_password(password)
    user = await firestore.create_user(
        email=email,
        password_hash=password_hash,
        created_by="cli_script"
    )

    print(f"\n{'='*50}")
    print("User created successfully!")
    print(f"{'='*50}")
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print(f"User ID:  {user.id}")
    print(f"{'='*50}")
    print("\nPlease save the password securely and send it to the user.")
    print("The password cannot be retrieved later - only reset.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Create a user for the Court Form OCR Testing App"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="User's email address"
    )
    parser.add_argument(
        "--password",
        required=False,
        help="User's password (optional - will generate if not provided)"
    )

    args = parser.parse_args()

    # Generate password if not provided
    password = args.password
    if not password:
        password = generate_password()
        print(f"Generated password: {password}")

    # Validate email format (basic check)
    if "@" not in args.email or "." not in args.email:
        print(f"Error: Invalid email format: {args.email}")
        sys.exit(1)

    # Create user
    asyncio.run(create_user(args.email, password))


if __name__ == "__main__":
    main()
