"""
Add Equipment Rental Line Items to Database
This links daily entries to equipment rental rates
"""

from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_PATH = "tracktm.db"


def add_equipment_rental_line_items_table():
    """Create table for equipment rental line items"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        print("Creating equipment_rental_line_items table...")
        print("=" * 80)

        # Create the table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS equipment_rental_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_entry_id INTEGER NOT NULL,
                equipment_rental_id INTEGER NOT NULL,
                quantity NUMERIC(10, 2) NOT NULL DEFAULT 1,
                rate_period VARCHAR(20) NOT NULL DEFAULT 'daily',
                unit_rate NUMERIC(10, 2) NOT NULL,
                total_amount NUMERIC(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(daily_entry_id) REFERENCES daily_entries(id) ON DELETE CASCADE,
                FOREIGN KEY(equipment_rental_id) REFERENCES equipment_rental_rates(id),
                UNIQUE(daily_entry_id, equipment_rental_id)
            )
        """
            )
        )

        conn.commit()
        print("✅ equipment_rental_line_items table created!")

        # Show schema
        result = conn.execute(text("PRAGMA table_info(equipment_rental_line_items)"))
        print("\n📊 Table Structure:")
        print("-" * 80)
        for row in result:
            null_text = "NOT NULL" if row[3] else ""
            default_text = f"DEFAULT {row[4]}" if row[4] else ""
            print(f"  {row[1]:<30} {row[2]:<20} {null_text:<10} {default_text}")
        print("-" * 80)


if __name__ == "__main__":
    add_equipment_rental_line_items_table()
