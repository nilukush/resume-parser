#!/usr/bin/env python3
"""
Script to URL-encode Supabase database password for safe use in connection strings.

This script encodes special characters in the password so they can be safely
used in PostgreSQL connection strings without breaking shell commands or URL parsing.

Usage:
    python scripts/encode_password.py
"""

import urllib.parse


def encode_password_for_connection_string(raw_password: str) -> str:
    """
    URL-encode a database password for use in connection strings.

    Characters that need encoding in URLs:
    - @ (separates credentials from host)
    - : (separates username from password)
    - / (path separator)
    - ? (query string start)
    - # (fragment identifier)
    - & (query parameter separator)
    - And other special characters

    Args:
        raw_password: The raw database password

    Returns:
        URL-encoded password safe for use in connection strings
    """
    # Use quote_plus to encode spaces as + and other special chars as %XX
    return urllib.parse.quote_plus(raw_password)


def main():
    # Your raw Supabase password
    raw_password = r"j<TN}Xs*ph%={>nb8L.w\clD&0C$W7!q?M':]Kt5"

    # Encode the password
    encoded_password = encode_password_for_connection_string(raw_password)

    print("=" * 80)
    print("SUPABASE PASSWORD ENCODING")
    print("=" * 80)
    print(f"\nRaw password (do NOT use in connection strings):")
    print(f"  {raw_password}")
    print(f"\nEncoded password (safe for connection strings):")
    print(f"  {encoded_password}")
    print("\n" + "=" * 80)
    print("CONNECTION STRINGS")
    print("=" * 80)

    # Supabase connection details
    host = "db.piqltpksqaldndikmaob.supabase.co"
    port = "5432"
    database = "postgres"
    user = "postgres"

    # Create connection strings
    database_url_async = (
        f"postgresql+asyncpg://postgres:{encoded_password}@{host}:{port}/{database}"
    )

    database_url_sync = (
        f"postgresql://postgres:{encoded_password}@{host}:{port}/{database}"
    )

    print(f"\n1. DATABASE_URL (for async operations):")
    print(f"   {database_url_async}")
    print(f"\n2. DATABASE_URL_SYNC (for sync operations):")
    print(f"   {database_url_sync}")
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Copy these connection strings")
    print("2. Go to your Vercel project dashboard")
    print("3. Update the following environment variables:")
    print("   - DATABASE_URL")
    print("   - DATABASE_URL_SYNC")
    print("4. Redeploy your Vercel project")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
