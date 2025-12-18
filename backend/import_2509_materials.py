#!/usr/bin/env python3
"""
Import Job-Specific Materials for Job 2509
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_session
from sqlalchemy import text

# Job 2509 Materials from your list
JOB_2509_MATERIALS = {
    "EQUIPMENT": [
        {"name": "Disc Pad Holder", "unit": "Each", "unit_price": 32.35},
        {"name": "Bristle wheels", "unit": "Each", "unit_price": 36.15},
        {"name": "Wire Cup Brushes-Home Depot", "unit": "Each", "unit_price": 23.47},
    ],
    "MATERIALS": [
        {"name": "Epoxy mastic 2 gal kit", "unit": "Kit", "unit_price": 145.48},
        {"name": "Zinc Kit", "unit": "Kit", "unit_price": 24.99},
        {"name": "Poly- 6 Mil", "unit": "Roll", "unit_price": 127.00},
        {"name": "White tape (4x108) roll", "unit": "Roll", "unit_price": 12.50},
        {"name": "Duct Tape", "unit": "Roll", "unit_price": 8.67},
        {"name": "Mek - 5 Gal", "unit": "Gallon", "unit_price": 19.85},
        {"name": "Reducer #58 5 gal", "unit": "Gallon", "unit_price": 27.32},
        {"name": "Jex Needle Supports", "unit": "Each", "unit_price": 55.80},
        {"name": "Jex needles/ 50 pc", "unit": "Box", "unit_price": 12.80},
    ],
    "PPE": [
        {"name": "Coveralls/ Tyvek", "unit": "Each", "unit_price": 4.98},
        {"name": "P100 filters", "unit": "Each", "unit_price": 8.87},
        {"name": "Safety Glasses/ Clear", "unit": "Each", "unit_price": 1.42},
        {"name": "Safety Glasses/ Tinted", "unit": "Each", "unit_price": 1.42},
        {"name": "Dbl eye face shield", "unit": "Each", "unit_price": 8.35},
        {"name": "Ear Plugs", "unit": "Pair", "unit_price": 0.18},
        {"name": "Gloves Blue & Yellow", "unit": "Pair", "unit_price": 6.15},
        {"name": "Gloves Gray & White", "unit": "Pair", "unit_price": 3.10},
        {"name": "Gloves Latex/ Nitrile", "unit": "Box", "unit_price": 14.20},
        {"name": "Head Socks", "unit": "Each", "unit_price": 0.81},
    ],
    "CONSUMABLES": [
        {"name": "AA Batteries- 10 pack", "unit": "Pack", "unit_price": 10.87},
        {"name": '4" roller naps', "unit": "Each", "unit_price": 9.64},
        {"name": 'Bent Rad 1"', "unit": "Each", "unit_price": 1.00},
        {"name": "Bent Rad Brushes 2 1/2", "unit": "Each", "unit_price": 2.25},
        {"name": "Bucket liners 5 gal", "unit": "Each", "unit_price": 3.28},
        {"name": "Bucket Liners 5 qt", "unit": "Each", "unit_price": 1.19},
        {"name": "Coating rem. Discs", "unit": "Each", "unit_price": 14.00},
        {"name": "Cut Off Wheels", "unit": "Each", "unit_price": 3.20},
        {"name": "Flapper Discs", "unit": "Each", "unit_price": 8.04},
        {"name": "Grinder Discs", "unit": "Each", "unit_price": 4.47},
        {"name": "Hand Pads/ Radnor", "unit": "Each", "unit_price": 1.82},
        {"name": "Kresto Quik Wipes", "unit": "Container", "unit_price": 31.93},
        {"name": "Sani Wipes", "unit": "Container", "unit_price": 9.54},
        {"name": "Rags", "unit": "Case", "unit_price": 51.56},
        {"name": "Trash Bags", "unit": "Box", "unit_price": 32.01},
        {"name": "Ice", "unit": "Bag", "unit_price": 2.99},
        {"name": "Ice 20 lb", "unit": "Bag", "unit_price": 5.99},
        {"name": "Water", "unit": "Case", "unit_price": 12.19},
        {"name": "Concentra- Blood lead", "unit": "Test", "unit_price": 136.00},
    ],
    "FUEL": [
        {"name": "Diesel", "unit": "Gallon", "unit_price": 3.99},
        {"name": "Gas", "unit": "Gallon", "unit_price": 2.99},
        {"name": "Def Fluid- 1 Gal", "unit": "Gallon", "unit_price": 9.99},
        {"name": "Def Fluid 2.5 Gal", "unit": "Jug", "unit_price": 15.48},
    ],
}


def create_job_materials_table(db):
    """Create job_materials table if it doesn't exist"""
    try:
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS job_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(50) NOT NULL,
                unit VARCHAR(50) NOT NULL,
                unit_price NUMERIC(10, 2) NOT NULL,
                active BOOLEAN DEFAULT 1,
                UNIQUE(job_number, name)
            )
        """
            )
        )

        db.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_job_materials_job 
            ON job_materials(job_number)
        """
            )
        )

        db.commit()
        print("✅ job_materials table created/verified")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        db.rollback()
        return False


def import_job_materials(job_number="2509"):
    """Import materials for job 2509"""
    db = get_session()

    print("=" * 70)
    print(f"Importing Materials for Job {job_number}")
    print("=" * 70)
    print()

    # Create table first
    if not create_job_materials_table(db):
        return

    imported_count = 0
    updated_count = 0

    for category, items in JOB_2509_MATERIALS.items():
        print(f"\n{category}: {len(items)} items")

        for item in items:
            try:
                # Check if material exists
                existing = db.execute(
                    text(
                        """
                    SELECT id FROM job_materials 
                    WHERE job_number = :job_number AND name = :name
                """
                    ),
                    {"job_number": job_number, "name": item["name"]},
                ).fetchone()

                if existing:
                    # Update existing
                    db.execute(
                        text(
                            """
                        UPDATE job_materials 
                        SET category = :category,
                            unit = :unit,
                            unit_price = :unit_price,
                            active = 1
                        WHERE job_number = :job_number AND name = :name
                    """
                        ),
                        {
                            "job_number": job_number,
                            "name": item["name"],
                            "category": category,
                            "unit": item["unit"],
                            "unit_price": item["unit_price"],
                        },
                    )
                    print(f"  🔄 Updated: {item['name']}")
                    updated_count += 1
                else:
                    # Insert new
                    db.execute(
                        text(
                            """
                        INSERT INTO job_materials 
                        (job_number, name, category, unit, unit_price, active)
                        VALUES 
                        (:job_number, :name, :category, :unit, :unit_price, 1)
                    """
                        ),
                        {
                            "job_number": job_number,
                            "name": item["name"],
                            "category": category,
                            "unit": item["unit"],
                            "unit_price": item["unit_price"],
                        },
                    )
                    print(
                        f"  ✅ Added: {item['name']} - ${item['unit_price']}/{item['unit']}"
                    )
                    imported_count += 1

            except Exception as e:
                print(f"  ❌ Error with {item['name']}: {e}")
                continue

    db.commit()

    print()
    print("=" * 70)
    print(f"Import Complete!")
    print(f"  New materials: {imported_count}")
    print(f"  Updated materials: {updated_count}")
    print("=" * 70)
    print()

    # Show summary
    total = db.execute(
        text(
            """
        SELECT category, COUNT(*) as count 
        FROM job_materials 
        WHERE job_number = :job_number AND active = 1
        GROUP BY category
        ORDER BY category
    """
        ),
        {"job_number": job_number},
    ).fetchall()

    print(f"Materials for Job {job_number}:")
    for row in total:
        print(f"  {row[0]}: {row[1]} items")

    db.close()


if __name__ == "__main__":
    import_job_materials()
