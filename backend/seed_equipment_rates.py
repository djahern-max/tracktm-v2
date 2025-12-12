"""
Seed Equipment Rental Rates - TSI 2022 Rates
Based on the uploaded 2022 rental rate sheet
"""

from sqlalchemy import create_engine, text
from datetime import date

DATABASE_PATH = "tracktm.db"

# TSI 2022 Equipment Rental Rates
TSI_2022_RATES = [
    # TRUCKS
    {
        "category": "TRUCKS",
        "name": "500 HP Tractor",
        "daily_rate": 995.00,
        "weekly_rate": 1829.00,
        "monthly_rate": 4877.00,
    },
    {
        "category": "TRUCKS",
        "name": "Freightliner Flatbed",
        "daily_rate": 655.00,
        "weekly_rate": 1894.00,
        "monthly_rate": 4877.00,
    },
    {
        "category": "TRUCKS",
        "name": "Pick Up Truck",
        "daily_rate": 175.00,
        "weekly_rate": 519.00,
        "monthly_rate": 2177.00,
    },
    # TRAILERS
    {
        "category": "TRAILERS",
        "name": "Landoll",
        "daily_rate": 391.00,
        "weekly_rate": 1150.00,
        "monthly_rate": 3200.00,
    },
    {
        "category": "TRAILERS",
        "name": "PJ Trailer",
        "daily_rate": 92.00,
        "weekly_rate": 232.00,
        "monthly_rate": 471.00,
    },
    {
        "category": "TRAILERS",
        "name": "Enclosed Trailer",
        "daily_rate": 82.00,
        "weekly_rate": 232.00,
        "monthly_rate": 471.00,
    },
    {
        "category": "TRAILERS",
        "name": "Goose Neck",
        "daily_rate": 82.00,
        "weekly_rate": 232.00,
        "monthly_rate": 471.00,
    },
    # COMPRESSORS
    {
        "category": "COMPRESSORS",
        "name": "1600 JD",
        "daily_rate": 926.00,
        "weekly_rate": 2600.00,
        "monthly_rate": 6995.00,
    },
    {
        "category": "COMPRESSORS",
        "name": "375 JD",
        "daily_rate": 290.00,
        "weekly_rate": None,
        "monthly_rate": 775.00,
    },
    {
        "category": "COMPRESSORS",
        "name": "185",
        "daily_rate": 166.00,
        "weekly_rate": None,
        "monthly_rate": 392.00,
    },
    # AIR ATTACHMENTS
    {
        "category": "AIR ATTACHMENTS",
        "name": "Air Dryer",
        "daily_rate": 41.00,
        "weekly_rate": 481.00,
        "monthly_rate": 1443.00,
    },
    {
        "category": "AIR ATTACHMENTS",
        "name": "Air Manifold",
        "daily_rate": 53.00,
        "weekly_rate": 141.00,
        "monthly_rate": 319.00,
    },
    {
        "category": "AIR ATTACHMENTS",
        "name": "Needle Gun",
        "daily_rate": 44.00,
        "weekly_rate": 102.00,
        "monthly_rate": 234.00,
    },
    {
        "category": "AIR ATTACHMENTS",
        "name": "Blast Pot",
        "daily_rate": 139.00,
        "weekly_rate": 430.00,
        "monthly_rate": 966.00,
    },
    # BLAST MACHINE
    {
        "category": "BLAST MACHINE",
        "name": "Six Man Super Unit",
        "daily_rate": 2700.00,
        "weekly_rate": 9500.00,
        "monthly_rate": 25400.00,
    },
    # DUST COLLECTORS
    {
        "category": "DUST COLLECTORS",
        "name": "40,000 CFM",
        "daily_rate": 926.00,
        "weekly_rate": 3100.00,
        "monthly_rate": 6995.00,
    },
    {
        "category": "DUST COLLECTORS",
        "name": "2000 CFM Electric Scrubber",
        "daily_rate": 75.00,
        "weekly_rate": 300.00,
        "monthly_rate": 675.00,
    },
    # DEHUMIDIFIERS
    {
        "category": "DEHUMIDIFIERS",
        "name": "15,000 CFM",
        "daily_rate": 196.00,
        "weekly_rate": 4118.00,
        "monthly_rate": 9600.00,
    },
    {
        "category": "DEHUMIDIFIERS",
        "name": "5,000 CFM",
        "daily_rate": 715.00,
        "weekly_rate": 1924.00,
        "monthly_rate": 5111.00,
    },
    # HEATERS
    {
        "category": "HEATERS",
        "name": "500,000 BTU IDF Heater",
        "daily_rate": None,
        "weekly_rate": None,
        "monthly_rate": None,
    },
    # VACUUMS
    {
        "category": "VACUUMS",
        "name": "Spartan HEPA Vacuum",
        "daily_rate": 29.00,
        "weekly_rate": 108.00,
        "monthly_rate": 269.00,
    },
    {
        "category": "VACUUMS",
        "name": "Portable HEPA Vacuum",
        "daily_rate": 24.00,
        "weekly_rate": 222.00,
        "monthly_rate": 431.00,
    },
    {
        "category": "VACUUMS",
        "name": "Shop Vacuum",
        "daily_rate": 29.00,
        "weekly_rate": 108.00,
        "monthly_rate": 269.00,
    },
    # PAINT PUMPS
    {
        "category": "PAINT PUMPS",
        "name": "Plural XM70",
        "daily_rate": 621.00,
        "weekly_rate": 1817.00,
        "monthly_rate": 4667.00,
    },
    {
        "category": "PAINT PUMPS",
        "name": "Graco Extreme",
        "daily_rate": 106.00,
        "weekly_rate": 391.00,
        "monthly_rate": 872.00,
    },
    {
        "category": "PAINT PUMPS",
        "name": "Electric Pump",
        "daily_rate": 75.00,
        "weekly_rate": 300.00,
        "monthly_rate": 675.00,
    },
    {
        "category": "PAINT PUMPS",
        "name": "Conventional Pot",
        "daily_rate": 75.00,
        "weekly_rate": 300.00,
        "monthly_rate": 675.00,
    },
    # POWER WASHERS
    {
        "category": "POWER WASHERS",
        "name": "1500 PSI up to 3000 PSI Cold",
        "daily_rate": 72.00,
        "weekly_rate": 266.00,
        "monthly_rate": 570.00,
    },
    {
        "category": "POWER WASHERS",
        "name": "3000 PSI Hot",
        "daily_rate": 139.00,
        "weekly_rate": 490.00,
        "monthly_rate": 966.00,
    },
    # MISC MACHINES/TOOLS
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Metalizing Set Up (Generator not included)",
        "daily_rate": 400.00,
        "weekly_rate": 1200.00,
        "monthly_rate": 3000.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Explosion Proof Light",
        "daily_rate": 125.00,
        "weekly_rate": 375.00,
        "monthly_rate": 495.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Explosion Proof Fan",
        "daily_rate": 125.00,
        "weekly_rate": 375.00,
        "monthly_rate": 495.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Electric Fan",
        "daily_rate": 25.00,
        "weekly_rate": 69.00,
        "monthly_rate": 180.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Rotary Hammer Drill",
        "daily_rate": 69.00,
        "weekly_rate": 202.00,
        "monthly_rate": 485.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "10 By 10 Equipment Berms",
        "daily_rate": 71.00,
        "weekly_rate": 209.00,
        "monthly_rate": 400.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Honda 5000 Generator",
        "daily_rate": 62.00,
        "weekly_rate": 240.00,
        "monthly_rate": 517.00,
    },
    {
        "category": "MISC MACHINES/TOOLS",
        "name": "Storage Container",
        "daily_rate": 36.00,
        "weekly_rate": 82.00,
        "monthly_rate": 180.00,
    },
]


def seed_equipment_rates():
    """Seed equipment rental rates table with TSI 2022 rates"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        print("Seeding TSI 2022 Equipment Rental Rates...")
        print("=" * 80)

        # Clear existing 2022 rates (in case re-running)
        conn.execute(text("DELETE FROM equipment_rental_rates WHERE year = '2022'"))
        conn.commit()

        # Insert rates
        count = 0
        for rate in TSI_2022_RATES:
            conn.execute(
                text(
                    """
                INSERT INTO equipment_rental_rates 
                (category, name, unit, daily_rate, weekly_rate, monthly_rate, year, effective_date, active)
                VALUES 
                (:category, :name, 'Day', :daily_rate, :weekly_rate, :monthly_rate, '2022', '2022-01-01', 1)
            """
                ),
                {
                    "category": rate["category"],
                    "name": rate["name"],
                    "daily_rate": rate["daily_rate"],
                    "weekly_rate": rate["weekly_rate"],
                    "monthly_rate": rate["monthly_rate"],
                },
            )
            count += 1

        conn.commit()

        print(f"✅ Successfully seeded {count} equipment rental rates!")
        print("=" * 80)

        # Show summary by category
        result = conn.execute(
            text(
                """
            SELECT category, COUNT(*) as count, 
                   MIN(daily_rate) as min_rate, 
                   MAX(daily_rate) as max_rate
            FROM equipment_rental_rates 
            WHERE year = '2022'
            GROUP BY category
            ORDER BY category
        """
            )
        )

        print("\n📊 Summary by Category:")
        print("-" * 80)
        print(f"{'Category':<25} {'Count':<10} {'Min Daily':<15} {'Max Daily':<15}")
        print("-" * 80)
        for row in result:
            min_rate = f"${row[2]:,.2f}" if row[2] else "N/A"
            max_rate = f"${row[3]:,.2f}" if row[3] else "N/A"
            print(f"{row[0]:<25} {row[1]:<10} {min_rate:<15} {max_rate:<15}")
        print("-" * 80)


if __name__ == "__main__":
    seed_equipment_rates()
