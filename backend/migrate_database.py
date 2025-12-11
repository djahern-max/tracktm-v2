"""
Migration Script - Add Multiple Employees Per Role Support
This script helps you transition from single to multiple employees per role
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from database import Base
import shutil
from datetime import datetime

DATABASE_PATH = "tracktm.db"
BACKUP_PATH = f"tracktm_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


def backup_database():
    """Create a backup of the current database"""
    if Path(DATABASE_PATH).exists():
        shutil.copy(DATABASE_PATH, BACKUP_PATH)
        print(f"✅ Backup created: {BACKUP_PATH}")
        return True
    else:
        print("ℹ️  No existing database found - will create new one")
        return False


def drop_unique_constraint():
    """Drop the unique constraint on labor_entries table"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        try:
            # SQLite doesn't support ALTER TABLE DROP CONSTRAINT directly
            # We need to recreate the table without the constraint

            print("🔄 Migrating labor_entries table...")

            # Create new table structure without constraint
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS labor_entries_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    daily_entry_id INTEGER NOT NULL,
                    labor_role_id INTEGER NOT NULL,
                    employee_name VARCHAR(255),
                    regular_hours NUMERIC(10, 2) DEFAULT 0 NOT NULL,
                    overtime_hours NUMERIC(10, 2) DEFAULT 0 NOT NULL,
                    night_shift BOOLEAN DEFAULT 0,
                    FOREIGN KEY(daily_entry_id) REFERENCES daily_entries (id) ON DELETE CASCADE,
                    FOREIGN KEY(labor_role_id) REFERENCES labor_roles (id)
                )
            """
                )
            )

            # Copy data from old table
            conn.execute(
                text(
                    """
                INSERT INTO labor_entries_new 
                SELECT id, daily_entry_id, labor_role_id, employee_name, 
                       regular_hours, overtime_hours, night_shift
                FROM labor_entries
            """
                )
            )

            # Drop old table
            conn.execute(text("DROP TABLE labor_entries"))

            # Rename new table
            conn.execute(text("ALTER TABLE labor_entries_new RENAME TO labor_entries"))

            conn.commit()
            print("✅ Migration complete! Unique constraint removed.")
            print("✅ You can now add multiple employees per role per day.")
            return True

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            return False


def verify_migration():
    """Verify the migration was successful"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        # Check table structure
        result = conn.execute(text("PRAGMA table_info(labor_entries)"))
        columns = [row[1] for row in result]

        print("\n📊 Verification:")
        print(f"   Columns: {', '.join(columns)}")

        # Check for any unique constraints
        result = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='labor_entries'"
            )
        )
        table_sql = result.fetchone()[0]

        if "UNIQUE" in table_sql or "unique_entry_labor" in table_sql:
            print("   ⚠️  Warning: Unique constraint may still exist")
            return False
        else:
            print("   ✅ No unique constraints found")
            return True


def main():
    print("=" * 60)
    print("TrackTM Database Migration")
    print("Multiple Employees Per Role Support")
    print("=" * 60)
    print()

    # Step 1: Backup
    print("Step 1: Backing up database...")
    has_data = backup_database()
    print()

    if not has_data:
        print("No migration needed - creating fresh database with updated schema")
        from database import init_db

        init_db()
        return

    # Step 2: Ask for confirmation
    print("⚠️  This migration will modify your database structure.")
    print("   A backup has been created, but please confirm:")
    response = input("\nProceed with migration? (yes/no): ")

    if response.lower() != "yes":
        print("Migration cancelled.")
        return

    print()

    # Step 3: Migrate
    print("Step 2: Removing unique constraint...")
    success = drop_unique_constraint()
    print()

    if not success:
        print("❌ Migration failed. Your original database is backed up at:")
        print(f"   {BACKUP_PATH}")
        return

    # Step 4: Verify
    print("Step 3: Verifying migration...")
    if verify_migration():
        print()
        print("=" * 60)
        print("✅ MIGRATION SUCCESSFUL!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Replace frontend/app.js with the new version")
        print("2. Replace frontend/styles.css with the new version")
        print("3. Restart your backend server")
        print("4. Hard refresh your browser (Ctrl+Shift+R)")
        print()
        print(f"Your old database is backed up at: {BACKUP_PATH}")
    else:
        print()
        print("⚠️  Migration completed but verification failed.")
        print("Please check your database manually.")


if __name__ == "__main__":
    main()
