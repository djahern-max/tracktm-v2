"""
TrackTM Import - Day 6: 11/24/2025 (Monday)
Job 2507 - PNSY DD #2 Stairwells T&M

Based on timesheet showing:
- Date: 11/24/25 MONDAY
- 6 workers back to full crew
- Justin Kneeland: PS/FM - 10 hrs straight
- Tim Mladek, Tom Guy, Ed Guy, Fred Angelosanto, Marineide Dantas: all with checkmarks
- Coating Application: Acrolon 100 HS
- Work Areas: Stairwell A (caulking & Acrolon 100 HS), Stairwell B (cleanup & removal)
"""

from database import (
    get_session,
    Material,
    LaborRole,
    DailyEntry,
    EntryLineItem,
    LaborEntry,
    EquipmentRentalEntry,
)
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime


def import_timesheet_entry(entry_data):
    """Import a single daily entry"""
    db = get_session()

    try:
        entry_date = datetime.strptime(entry_data["date"], "%Y-%m-%d").date()

        print(f"\n{'='*60}")
        print(f"Importing entry for {entry_data['job_number']} on {entry_date}")
        print(f"{'='*60}")

        # Check if entry already exists
        existing_entry = (
            db.query(DailyEntry)
            .filter(
                DailyEntry.job_number == entry_data["job_number"],
                DailyEntry.entry_date == entry_date,
            )
            .first()
        )

        if existing_entry:
            print(f"[WARNING] Entry already exists for this date!")
            print(f"[INFO] Deleting existing entry and all related items...")

            # Delete existing related items
            db.query(LaborEntry).filter(
                LaborEntry.daily_entry_id == existing_entry.id
            ).delete()
            db.query(EntryLineItem).filter(
                EntryLineItem.daily_entry_id == existing_entry.id
            ).delete()
            db.query(EquipmentRentalEntry).filter(
                EquipmentRentalEntry.daily_entry_id == existing_entry.id
            ).delete()

            # Delete the daily entry itself
            db.delete(existing_entry)
            db.flush()
            print(f"[OK] Deleted existing entry")

        daily_entry = DailyEntry(
            job_number=entry_data["job_number"], entry_date=entry_date
        )
        db.add(daily_entry)
        db.flush()

        print(f"[OK] Created daily entry (ID: {daily_entry.id})")

        # Add labor entries
        labor_total = 0
        if "labor" in entry_data:
            print(f"\n--- LABOR ({len(entry_data['labor'])} workers) ---")
            for labor in entry_data["labor"]:
                role = (
                    db.query(LaborRole).filter(LaborRole.name == labor["role"]).first()
                )
                if not role:
                    print(f"[ERROR] Labor role '{labor['role']}' not found!")
                    continue

                labor_entry = LaborEntry(
                    daily_entry_id=daily_entry.id,
                    labor_role_id=role.id,
                    employee_name=labor.get("employee_name"),
                    regular_hours=Decimal(str(labor.get("regular_hours", 0))),
                    overtime_hours=Decimal(str(labor.get("overtime_hours", 0))),
                    night_shift=labor.get("night_shift", False),
                )
                db.add(labor_entry)

                cost = float(labor_entry.regular_hours) * float(role.straight_rate)
                cost += float(labor_entry.overtime_hours) * float(role.overtime_rate)
                if labor_entry.night_shift:
                    cost += (
                        float(labor_entry.regular_hours)
                        + float(labor_entry.overtime_hours)
                    ) * 2.00

                labor_total += cost
                print(
                    f"  [OK] {labor.get('employee_name', 'Unknown')}: {labor.get('regular_hours', 0)} reg + {labor.get('overtime_hours', 0)} OT = ${cost:,.2f}"
                )

        print(f"Labor subtotal: ${labor_total:,.2f}")

        # Add materials
        materials_total = 0
        if "materials" in entry_data:
            print(f"\n--- MATERIALS ({len(entry_data['materials'])} items) ---")
            for mat in entry_data["materials"]:
                material = (
                    db.query(Material).filter(Material.name == mat["name"]).first()
                )
                if not material:
                    print(f"[WARNING] Material '{mat['name']}' not found - skipping")
                    continue

                unit_price = mat.get("unit_price", float(material.unit_price))

                line_item = EntryLineItem(
                    daily_entry_id=daily_entry.id,
                    material_id=material.id,
                    quantity=Decimal(str(mat["quantity"])),
                    unit_price=Decimal(str(unit_price)),
                )
                db.add(line_item)

                total = float(mat["quantity"]) * unit_price
                materials_total += total
                print(
                    f"  [OK] {mat['name']}: {mat['quantity']} × ${unit_price} = ${total:,.2f}"
                )

        print(f"Materials subtotal: ${materials_total:,.2f}")

        # Add equipment rentals
        equipment_total = 0
        if "equipment" in entry_data:
            print(f"\n--- EQUIPMENT ({len(entry_data['equipment'])} items) ---")
            for equip in entry_data["equipment"]:
                result = db.execute(
                    text(
                        """
                        SELECT id, name, category, daily_rate, weekly_rate, monthly_rate
                        FROM equipment_rental_rates
                        WHERE name = :name AND active = 1
                    """
                    ),
                    {"name": equip["name"]},
                ).fetchone()

                if not result:
                    print(f"[WARNING] Equipment '{equip['name']}' not found - skipping")
                    continue

                rate_period = equip.get("rate_period", "daily")
                if rate_period == "weekly":
                    unit_rate = result[4]
                elif rate_period == "monthly":
                    unit_rate = result[5]
                else:
                    unit_rate = result[3]

                equipment_entry = EquipmentRentalEntry(
                    daily_entry_id=daily_entry.id,
                    equipment_rental_id=result[0],
                    quantity=Decimal(str(equip["quantity"])),
                    unit_rate=Decimal(str(unit_rate)),
                    equipment_name=result[1],
                    equipment_category=result[2],
                    unit=(
                        "Day"
                        if rate_period == "daily"
                        else ("Week" if rate_period == "weekly" else "Month")
                    ),
                )
                db.add(equipment_entry)

                total = float(equip["quantity"]) * float(unit_rate)
                equipment_total += total
                print(
                    f"  [OK] {equip['name']}: {equip['quantity']} × ${unit_rate} = ${total:,.2f}"
                )

        print(f"Equipment subtotal: ${equipment_total:,.2f}")

        db.commit()

        grand_total = labor_total + materials_total + equipment_total
        print(f"\n{'='*60}")
        print(f"[SUCCESS] Entry imported! Total: ${grand_total:,.2f}")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to import entry: {e}")
        db.rollback()
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


# ============================================
# Day 6: Monday 11/24/2025
# 6 workers - full crew back
# Justin Kneeland: PS/FM - 10 hrs straight, 0 OT
# All others: 10 hrs straight (checkmarks shown)
# Coating: Acrolon 100 HS application
# ============================================

ENTRY_DATA = {
    "job_number": "2507",
    "date": "2025-11-24",
    # LABOR - 6 workers, all 10 hours straight time
    "labor": [
        {
            "role": "Painter",
            "employee_name": "Justin Kneeland",
            "regular_hours": 10,
            "overtime_hours": 0,
        },
        {
            "role": "Painter",
            "employee_name": "Tim Mladek",
            "regular_hours": 10,
            "overtime_hours": 0,
        },
        {
            "role": "Painter",
            "employee_name": "Thomas Guy",
            "regular_hours": 10,
            "overtime_hours": 0,
        },
        {
            "role": "Painter",
            "employee_name": "Edward Guy",
            "regular_hours": 10,
            "overtime_hours": 0,
        },
        {
            "role": "Painter",
            "employee_name": "Frederick Angelosanto",
            "regular_hours": 10,
            "overtime_hours": 0,
        },
        {
            "role": "Painter",
            "employee_name": "Marineide Dantas",
            "regular_hours": 10,
            "overtime_hours": 0,
        },
    ],
    # MATERIALS - From timesheet page 2
    # Materials: Tubes Caulking (4), Acrolon 100 (20 gallons)
    # Consumables: Pair P100 Dust Filters, Roll Tyvek Bags, 5 Gallon Liners, Box Rags,
    #              Box Paint Strainers, Box AAA Batteries
    # PPE: Tyvek Coveralls, Pair Safety Glasses, Pair Gloves, Head Socks, Box Rubber Gloves
    "materials": [
        # Materials section
        {
            "name": "Sherwin Williams Power House Caulk",
            "quantity": 4,
        },  # TUBES CAULKING (4)
        {"name": "Acrolon Paint", "quantity": 20},  # ACROLON 100 (GALLONS) - 20
        # Consumables
        {"name": "P100 Filter Particulate", "quantity": 4},  # PAIR P100 DUST FILTERS
        {"name": "Gold Trash Bags", "quantity": 1},  # ROLL TYVEK BAGS
        {"name": "Bucket Liners 5 Gallon", "quantity": 5},  # 5 GALLON LINERS
        {"name": "Rags", "quantity": 1},  # BOX RAGS
        {"name": "Paint Strainers", "quantity": 1},  # BOX PAINT STRAINERS
        {"name": "AAA Batteries", "quantity": 1},  # BOX AAA BATTERIES
        # PPE
        {"name": "Coveralls 2XL", "quantity": 5},  # TYVEK COVERALLS
        {"name": "Safety Glasses", "quantity": 5},  # PAIR SAFETY GLASSES
        {
            "name": "Gloves Nitrile Latex Disposable",
            "quantity": 6,
        },  # 5 PAIR GLOVES + 1 BOX
        {"name": "Head Socks", "quantity": 5},  # HEAD SOCKS
    ],
    # EQUIPMENT - From timesheet page 2
    "equipment": [
        {"name": "Ford F250", "quantity": 1, "rate_period": "daily"},
        {"name": "PJ Trailer", "quantity": 1, "rate_period": "daily"},
        {"name": "DH Units", "quantity": 4, "rate_period": "daily"},
        {"name": "DH Hoses", "quantity": 4, "rate_period": "daily"},
        {"name": "Power Cable", "quantity": 8, "rate_period": "daily"},
        {"name": "Graco Extreme", "quantity": 1, "rate_period": "daily"},
        {"name": "Caulking Guns", "quantity": 2, "rate_period": "daily"},
    ],
}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("IMPORTING SINGLE DAY: 11/24/2025")
    print("=" * 60)

    if import_timesheet_entry(ENTRY_DATA):
        print("\n✅ Import successful!")
    else:
        print("\n❌ Import failed!")
