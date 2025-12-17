#!/usr/bin/env python3
"""
Test script to verify dehumidifier aggregation logic
Run this from your backend directory with: python test_dehumidifier.py
"""

import sys

sys.path.insert(0, "/mnt/project")

from database import get_session, DailyEntry
from datetime import datetime


def test_dehumidifier_aggregation():
    db = get_session()

    # Query for job 312550, date range 11/18 - 12/10
    start_date = "2025-11-18"
    end_date = "2025-12-10"
    job_number = "312550"

    query = db.query(DailyEntry).filter(DailyEntry.job_number == job_number)
    query = query.filter(DailyEntry.entry_date >= start_date)
    query = query.filter(DailyEntry.entry_date <= end_date)
    entries = query.order_by(DailyEntry.entry_date).all()

    print(f"Found {len(entries)} entries for job {job_number}")
    print(f"Date range: {start_date} to {end_date}\n")

    # Check equipment rentals
    equipment_base = 0.0
    dehumidifier_total = 0.0

    for entry in entries:
        print(f"Entry Date: {entry.entry_date}")
        print(f"  Equipment items: {len(entry.equipment_rental_items)}")

        for item in entry.equipment_rental_items:
            print(f"    - {item.equipment_name}: ${item.total_amount}")

            # Check for dehumidifier
            if (
                "dehumidifier" in item.equipment_name.lower()
                and "rental" in item.equipment_name.lower()
            ):
                print(f"      ✓ IDENTIFIED AS DEHUMIDIFIER (pass-through)")
                dehumidifier_total += item.total_amount
            else:
                print(f"      → Regular equipment (will get markup)")
                equipment_base += item.total_amount
        print()

    print("=" * 60)
    print(f"Equipment with markup: ${equipment_base:,.2f}")
    print(f"Dehumidifier (pass-through): ${dehumidifier_total:,.2f}")
    print("=" * 60)

    if dehumidifier_total > 0:
        print("\n✓ SUCCESS: Dehumidifier should appear as separate line item!")
    else:
        print("\n✗ ERROR: Dehumidifier not found!")

    db.close()


if __name__ == "__main__":
    test_dehumidifier_aggregation()
