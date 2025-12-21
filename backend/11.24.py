#!/usr/bin/env python3
"""
Manually delete ALL data for Job 2509, 11-24-2025
Run this before running 11.24.py
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_session
from sqlalchemy import text

JOB_NUMBER = "2509"
ENTRY_DATE = "2025-11-24"


def delete_entry():
    """Delete entry and all related records"""
    db = get_session()

    print("=" * 70)
    print(f"DELETING ALL DATA for Job {JOB_NUMBER}, Date {ENTRY_DATE}")
    print("=" * 70)
    print()

    # Find the entry
    existing = db.execute(
        text(
            """
            SELECT id FROM daily_entries
            WHERE job_number = :job AND entry_date = :date
        """
        ),
        {"job": JOB_NUMBER, "date": ENTRY_DATE},
    ).fetchone()

    if not existing:
        print("✅ No entry found - nothing to delete!")
        db.close()
        return

    entry_id = existing[0]
    print(f"🔍 Found entry ID: {entry_id}")
    print()

    # Delete all related records
    print("🗑️  Deleting materials...")
    result = db.execute(
        text("DELETE FROM entry_line_items WHERE daily_entry_id = :id"),
        {"id": entry_id},
    )
    print(f"   ✅ Deleted {result.rowcount} material line items")

    print("🗑️  Deleting labor...")
    result = db.execute(
        text("DELETE FROM labor_entries WHERE daily_entry_id = :id"), {"id": entry_id}
    )
    print(f"   ✅ Deleted {result.rowcount} labor entries")

    print("🗑️  Deleting equipment...")
    result = db.execute(
        text("DELETE FROM equipment_rental_items WHERE daily_entry_id = :id"),
        {"id": entry_id},
    )
    print(f"   ✅ Deleted {result.rowcount} equipment entries")

    print("🗑️  Deleting daily entry...")
    result = db.execute(
        text("DELETE FROM daily_entries WHERE id = :id"), {"id": entry_id}
    )
    print(f"   ✅ Deleted daily entry")

    # Commit
    db.commit()
    print()
    print("=" * 70)
    print("✅ ALL DATA DELETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nYou can now run: python 11.24.py")

    db.close()


if __name__ == "__main__":
    delete_entry()
