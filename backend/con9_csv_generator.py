"""
Con9 CSV Export Generator
Exports daily timesheet data in a format that can be imported into Con9 forms
"""

import csv
from io import StringIO
from decimal import Decimal


def generate_con9_csv(entry_data, job_info):
    """
    Generate CSV export for Con9 form

    Args:
        entry_data: Daily entry data from database (includes line_items, labor_entries, equipment_rental_items)
        job_info: Dict with job_number, entry_date, job_name, etc.

    Returns:
        StringIO buffer containing CSV data
    """
    output = StringIO()
    writer = csv.writer(output)

    # Header Information
    writer.writerow(["CON9 DAILY REPORT EXPORT"])
    writer.writerow(["Job Number:", job_info.get("job_number", "")])
    writer.writerow(["Job Name:", job_info.get("job_name", "")])
    writer.writerow(["Date:", job_info.get("entry_date", "")])
    writer.writerow(
        ["Contractor:", job_info.get("contractor", "Tri-State Painting, LLC")]
    )
    writer.writerow([])

    # ============================================
    # LABOR SECTION
    # ============================================
    writer.writerow(["LABOR SECTION"])
    writer.writerow(
        [
            "Class",
            "Employee",
            "Total Hours",
            "Regular Rate",
            "OT Rate",
            "Regular Hours",
            "OT Hours",
            "Regular Amount",
            "OT Amount",
            "Total Amount",
        ]
    )

    labor_total = Decimal("0")
    total_hours = Decimal("0")

    for labor in entry_data.get("labor_entries", []):
        employee_name = labor.get("employee_name", "Unknown")
        role_name = labor.get("role_name", "Labor")
        reg_hours = Decimal(str(labor.get("regular_hours", 0)))
        ot_hours = Decimal(str(labor.get("overtime_hours", 0)))
        straight_rate = Decimal(str(labor.get("straight_rate", 0)))
        overtime_rate = Decimal(str(labor.get("overtime_rate", 0)))

        reg_amount = reg_hours * straight_rate
        ot_amount = ot_hours * overtime_rate
        total_amount = reg_amount + ot_amount
        hours = reg_hours + ot_hours

        labor_total += total_amount
        total_hours += hours

        writer.writerow(
            [
                role_name,
                employee_name,
                float(hours),
                float(straight_rate),
                float(overtime_rate),
                float(reg_hours),
                float(ot_hours),
                float(reg_amount),
                float(ot_amount),
                float(total_amount),
            ]
        )

    # Labor Summary Calculations
    writer.writerow([])
    writer.writerow(["LABOR SUMMARY"])
    writer.writerow(["Description", "Calculation", "Amount"])

    # Row 1: Total Labor
    writer.writerow(["1. Total Labor", "", float(labor_total)])

    # Row 2: Health & Welfare ($12.75/hr)
    hw_rate = Decimal("12.75")
    health_welfare = total_hours * hw_rate
    writer.writerow(
        [
            "2. Health & Welfare",
            f"{float(total_hours)} hrs × ${float(hw_rate)}/hr",
            float(health_welfare),
        ]
    )

    # Row 3: Pension ($13.33/hr)
    pension_rate = Decimal("13.33")
    pension = total_hours * pension_rate
    writer.writerow(
        [
            "3. Pension",
            f"{float(total_hours)} hrs × ${float(pension_rate)}/hr",
            float(pension),
        ]
    )

    # Row 4: Insurance & Taxes (you'll fill this in manually)
    writer.writerow(["4. Insurance & Taxes on Item 1", "Manual Entry Required", ""])

    # Row 5: 20% of Items 1+2+3
    subtotal_123 = labor_total + health_welfare + pension
    markup_20 = subtotal_123 * Decimal("0.20")
    writer.writerow(
        ["5. 20% of Items 1+2+3", f"20% × ${float(subtotal_123)}", float(markup_20)]
    )

    labor_subtotal = labor_total + health_welfare + pension + markup_20
    writer.writerow(["LABOR SUBTOTAL (without Item 4)", "", float(labor_subtotal)])
    writer.writerow([])

    # ============================================
    # MATERIALS SECTION
    # ============================================
    writer.writerow(["MATERIALS SECTION"])
    writer.writerow(["Description", "Quantity", "Unit", "Unit Price", "Amount"])

    materials_total = Decimal("0")

    for item in entry_data.get("line_items", []):
        material_name = item.get("material_name", "Unknown")
        quantity = Decimal(str(item.get("quantity", 0)))
        unit = item.get("unit", "Each")
        unit_price = Decimal(str(item.get("unit_price", 0)))
        total_amount = quantity * unit_price

        materials_total += total_amount

        writer.writerow(
            [
                material_name,
                float(quantity),
                unit,
                float(unit_price),
                float(total_amount),
            ]
        )

    # Materials Summary
    writer.writerow([])
    writer.writerow(["MATERIALS SUMMARY"])
    writer.writerow(["Description", "Calculation", "Amount"])
    writer.writerow(["Material Total", "", float(materials_total)])

    # 15% Material Markup
    materials_markup = materials_total * Decimal("0.15")
    writer.writerow(
        [
            "15% Material Markup",
            f"15% × ${float(materials_total)}",
            float(materials_markup),
        ]
    )

    materials_subtotal = materials_total + materials_markup
    writer.writerow(["MATERIALS SUBTOTAL", "", float(materials_subtotal)])
    writer.writerow([])

    # ============================================
    # EQUIPMENT SECTION
    # ============================================
    writer.writerow(["EQUIPMENT SECTION"])
    writer.writerow(
        [
            "Description",
            "Size & Class",
            "Pieces",
            "Hours",
            "Rate",
            "Rate Type",
            "Amount",
        ]
    )

    equipment_total = Decimal("0")

    for equip in entry_data.get("equipment_rental_items", []):
        equipment_name = equip.get("equipment_name", "Unknown")
        quantity = Decimal(str(equip.get("quantity", 0)))
        unit = equip.get("unit", "Day")
        unit_rate = Decimal(str(equip.get("unit_rate", 0)))
        total_amount = quantity * unit_rate

        equipment_total += total_amount

        writer.writerow(
            [
                equipment_name,
                "",  # Size & Class - can be filled in manually
                1,  # Pieces
                float(quantity),
                float(unit_rate),
                unit,
                float(total_amount),
            ]
        )

    # Equipment Summary
    writer.writerow([])
    writer.writerow(["EQUIPMENT SUMMARY"])
    writer.writerow(["Description", "Amount"])
    writer.writerow(["Equipment Total", float(equipment_total)])
    writer.writerow([])

    # ============================================
    # GRAND TOTAL
    # ============================================
    writer.writerow(["CONTRACTOR TOTAL"])
    writer.writerow(["Labor Subtotal (without Item 4)", float(labor_subtotal)])
    writer.writerow(["Materials Subtotal", float(materials_subtotal)])
    writer.writerow(["Equipment Total", float(equipment_total)])
    writer.writerow([])

    # Note: Insurance & Taxes (Item 4) needs to be added manually
    writer.writerow(
        ["NOTE: Add Insurance & Taxes (Item 4) manually to get final total"]
    )
    writer.writerow(
        [
            "Subtotal Before Item 4",
            float(labor_subtotal + materials_subtotal + equipment_total),
        ]
    )

    output.seek(0)
    return output


def format_con9_filename(job_number, entry_date):
    """Generate filename for Con9 CSV export"""
    return f"Con9_{job_number}_{entry_date}.csv"
