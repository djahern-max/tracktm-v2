"""
Add Missing Items for PNSY Job
Based on 11/19/2025 timesheet gaps
"""

from sqlalchemy import create_engine, text

DATABASE_PATH = "tracktm.db"

MISSING_ITEMS = [
    # Equipment that's not in the current catalog
    {
        "category": "EQUIPMENT",
        "name": "Graco Extreme Paint Pump",
        "unit": "Day",
        "unit_price": 106.00,  # From 2022 rental rates
    },
    {
        "category": "EQUIPMENT",
        "name": "DH Hoses",
        "unit": "Day",
        "unit_price": 25.00,  # Estimate - need actual rate
    },
    {
        "category": "EQUIPMENT",
        "name": "Power Angle Brush Unit",
        "unit": "Day",
        "unit_price": 50.00,  # Estimate - need actual rate
    },
    # Materials - Acrolon 100 coating (midpoint of $130-200 range)
    {
        "category": "MATERIALS",
        "name": "Acrolon 100 (Gallon)",
        "unit": "Gallon",
        "unit_price": 165.00,  # Midpoint - verify actual cost later
    },
]


def add_missing_items():
    """Add missing items to materials catalog"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        print("Adding missing items to materials catalog...")
        print("=" * 80)

        added = 0
        skipped = 0

        for item in MISSING_ITEMS:
            # Check if item already exists
            result = conn.execute(
                text(
                    """
                SELECT id FROM materials WHERE name = :name
            """
                ),
                {"name": item["name"]},
            )

            if result.fetchone():
                print(f"⏭️  Skipped (exists): {item['name']}")
                skipped += 1
                continue

            # Insert new item
            conn.execute(
                text(
                    """
                INSERT INTO materials (name, category, unit, unit_price)
                VALUES (:name, :category, :unit, :unit_price)
            """
                ),
                item,
            )

            print(
                f"✅ Added: {item['name']} - ${item['unit_price']:.2f}/{item['unit']}"
            )
            added += 1

        conn.commit()

        print("=" * 80)
        print(f"Added: {added} items")
        print(f"Skipped: {skipped} items")
        print("=" * 80)

        # Show current equipment in catalog
        print("\n🚛 EQUIPMENT in Catalog:")
        print("-" * 80)
        result = conn.execute(
            text(
                """
            SELECT name, unit, unit_price
            FROM materials
            WHERE category = 'EQUIPMENT'
            ORDER BY name
        """
            )
        )

        for row in result:
            print(f"  {row[0]:<45} ${row[2]:>7.2f}/{row[1]}")
        print("-" * 80)


if __name__ == "__main__":
    add_missing_items()
