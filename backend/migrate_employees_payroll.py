#!/usr/bin/env python3
"""
Migration: Add/Update employees table with payroll fields
FIXED VERSION - Always checks labor_entries table
"""

import sqlite3
import os
from pathlib import Path


def migrate():
    # Find database in current directory
    db_path = Path(__file__).parent / "tracktm.db"

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print(f"   Looking in: {db_path.parent}")
        print(f"   Please run this script from your backend directory")
        return False

    print(f"📁 Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # ============================================
        # PART 1: Check and migrate employees table
        # ============================================
        cursor.execute("PRAGMA table_info(employees)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        if not columns:
            print("❌ employees table does not exist")
            print("   Creating new employees table with payroll fields...")
            cursor.execute(
                """
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_number VARCHAR(50) NOT NULL UNIQUE,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    "union" VARCHAR(50) NOT NULL,
                    regular_rate NUMERIC(10, 2) NOT NULL,
                    overtime_rate NUMERIC(10, 2) NOT NULL,
                    health_welfare NUMERIC(10, 2) NOT NULL,
                    pension NUMERIC(10, 2) NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    notes TEXT
                )
            """
            )
            conn.commit()
            print("✅ New employees table created")
        elif "employee_number" in columns:
            print("✅ employees table already has payroll fields")
        else:
            print("⚠️  Old employees table found - needs migration")

            # 1. Rename old table
            cursor.execute("ALTER TABLE employees RENAME TO employees_old")

            # 2. Create new table with payroll fields
            cursor.execute(
                """
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_number VARCHAR(50) NOT NULL UNIQUE,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    "union" VARCHAR(50) NOT NULL,
                    regular_rate NUMERIC(10, 2) NOT NULL,
                    overtime_rate NUMERIC(10, 2) NOT NULL,
                    health_welfare NUMERIC(10, 2) NOT NULL,
                    pension NUMERIC(10, 2) NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    notes TEXT
                )
            """
            )

            # 3. Try to migrate data if old table had name field
            if "name" in columns:
                print("⚠️  Old table had simple 'name' field")
                print("   Cannot auto-migrate - you'll need to re-import employee data")
                print("   Run: python import_employees.py")

            # 4. Drop old table
            cursor.execute("DROP TABLE employees_old")
            conn.commit()
            print("✅ Employees table migration complete")

        # Show final schema
        cursor.execute("PRAGMA table_info(employees)")
        print("\n📋 Employees table schema:")
        for col in cursor.fetchall():
            nullable = "NOT NULL" if col[3] else "NULL"
            print(f"   {col[1]:20} {col[2]:20} {nullable}")

        # ============================================
        # PART 2: ALWAYS check labor_entries table
        # ============================================
        print("\n" + "=" * 70)
        print("Checking labor_entries table...")
        print("=" * 70)

        cursor.execute("PRAGMA table_info(labor_entries)")
        labor_cols = [col[1] for col in cursor.fetchall()]

        if "employee_id" not in labor_cols:
            print("\n➕ Adding employee_id to labor_entries...")
            cursor.execute(
                """
                ALTER TABLE labor_entries
                ADD COLUMN employee_id INTEGER
                REFERENCES employees(id)
            """
            )
            conn.commit()
            print("✅ employee_id column added to labor_entries")
        else:
            print("\n✅ labor_entries already has employee_id column")

        # Show final labor_entries schema
        cursor.execute("PRAGMA table_info(labor_entries)")
        print("\n📋 Labor_entries table schema:")
        for col in cursor.fetchall():
            nullable = "NOT NULL" if col[3] else "NULL"
            print(f"   {col[1]:20} {col[2]:20} {nullable}")

        conn.commit()
        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        import traceback

        traceback.print_exc()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("TrackTM Database Migration: Employees Table with Payroll Fields")
    print("FIXED VERSION - Always checks labor_entries table")
    print("=" * 70)
    print()

    success = migrate()

    if success:
        print("\n🎉 Migration complete!")
        print("\nNext steps:")
        print("  1. Run: python import_employees.py (if needed)")
        print("  2. Restart your FastAPI server")
    else:
        print("\n⚠️  Migration failed - please check errors above")
