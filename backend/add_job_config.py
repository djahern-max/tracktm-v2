"""
Add Job-Specific Markup Configuration
This allows different markup rates per job/contract
"""

from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_PATH = "tracktm.db"


def add_job_config_table():
    """Create job configuration table for contract-specific settings"""
    engine = create_engine(f"sqlite:///./{DATABASE_PATH}")

    with engine.connect() as conn:
        print("Creating job_config table for contract-specific settings...")

        # Create job configuration table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS job_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number VARCHAR(50) NOT NULL UNIQUE,
                job_name VARCHAR(255),
                client_name VARCHAR(255),
                contract_type VARCHAR(50) DEFAULT 'T&M',
                equipment_markup_pct NUMERIC(5, 2) DEFAULT 0.00,
                materials_markup_pct NUMERIC(5, 2) DEFAULT 0.00,
                apply_ten_and_ten BOOLEAN DEFAULT 0,
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        conn.commit()
        print("✅ job_config table created!")

        # Add PNSY job configuration
        print("\nAdding PNSY Job #2507 configuration...")
        conn.execute(
            text(
                """
            INSERT OR REPLACE INTO job_config 
            (job_number, job_name, client_name, contract_type, apply_ten_and_ten, notes)
            VALUES 
            ('2507', 'PNSY DD #2 Stairwells A&B', 'AZ Corp / Cianbro', 'T&M', 1, 
             'Contract specifies: Equipment & Supplies Cost plus 10% OH and 10% Profit (Ten and Ten)')
        """
            )
        )

        conn.commit()
        print("✅ Job #2507 configured with 'Ten and Ten' markup!")

        # Show the configuration
        result = conn.execute(
            text(
                """
            SELECT job_number, job_name, client_name, apply_ten_and_ten, notes
            FROM job_config
            WHERE job_number = '2507'
        """
            )
        )

        print("\n📋 Job Configuration:")
        print("-" * 80)
        for row in result:
            print(f"Job Number: {row[0]}")
            print(f"Job Name: {row[1]}")
            print(f"Client: {row[2]}")
            print(f"Apply Ten & Ten: {'YES' if row[3] else 'NO'}")
            print(f"Notes: {row[4]}")
        print("-" * 80)


def calculate_ten_and_ten(cost):
    """
    Calculate 'Ten and Ten' markup
    First 10%, then another 10% on the result
    Formula: cost * 1.10 * 1.10 = cost * 1.21
    """
    return cost * 1.21


def calculate_simple_markup(cost, markup_pct):
    """Calculate simple percentage markup"""
    return cost * (1 + markup_pct / 100)


if __name__ == "__main__":
    add_job_config_table()

    # Show example calculations
    print("\n💰 Markup Calculation Examples:")
    print("-" * 80)
    print(f"Equipment Cost: $175.00/day (Pickup Truck)")
    print(f"  With Ten & Ten: ${calculate_ten_and_ten(175.00):.2f}")
    print(f"  With 20% markup: ${calculate_simple_markup(175.00, 20):.2f}")
    print()
    print(f"Equipment Cost: $62.00/day (Generator)")
    print(f"  With Ten & Ten: ${calculate_ten_and_ten(62.00):.2f}")
    print(f"  With 20% markup: ${calculate_simple_markup(62.00, 20):.2f}")
    print("-" * 80)
