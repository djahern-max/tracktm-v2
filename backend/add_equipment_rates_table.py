"""
Add Equipment Rental Rates Table
This creates a flexible structure for tracking equipment rental rates
that can be customized per contractor/company
"""

from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_PATH = "tracktm.db"


def add_equipment_rates_table():
    """Add equipment_rental_rates table to database"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        print("Creating equipment_rental_rates table...")

        # Create the table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS equipment_rental_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                unit VARCHAR(50) NOT NULL DEFAULT 'Day',
                daily_rate NUMERIC(10, 2),
                weekly_rate NUMERIC(10, 2),
                monthly_rate NUMERIC(10, 2),
                year VARCHAR(4) NOT NULL,
                effective_date DATE,
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, name, year)
            )
        """
            )
        )

        conn.commit()
        print("✅ equipment_rental_rates table created successfully!")

        # Show the schema
        result = conn.execute(text("PRAGMA table_info(equipment_rental_rates)"))
        print("\n📊 Table Structure:")
        print("-" * 80)
        for row in result:
            print(f"  {row[1]:<20} {row[2]:<15} {'NOT NULL' if row[3] else ''}")
        print("-" * 80)


if __name__ == "__main__":
    add_equipment_rates_table()
