#!/usr/bin/env python3
"""
Import Employee Payroll Data
Populates employees table with union workers and their rates
"""

import sys
import os

# Add the current directory to the path so we can import database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_session, Employee
from decimal import Decimal

# Employee data from your payroll spreadsheet
EMPLOYEES_DATA = [
    {
        "employee_number": "10551",
        "first_name": "Ace",
        "last_name": "Moses",
        "union": "DC9",
        "regular_rate": 104.75,
        "overtime_rate": 157.13,
        "health_welfare": 12.75,
        "pension": 13.33,
    },
    {
        "employee_number": "10306",
        "first_name": "Mark",
        "last_name": "Ruge",
        "union": "DC35",
        "regular_rate": 87.89,
        "overtime_rate": 131.84,
        "health_welfare": 10.30,
        "pension": 11.95,
    },
    {
        "employee_number": "10585",
        "first_name": "Juan",
        "last_name": "Estrada",
        "union": "DC11",
        "regular_rate": 84.73,
        "overtime_rate": 127.10,
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10578",
        "first_name": "Jael",
        "last_name": "Garcia",
        "union": "DC11",
        "regular_rate": 70.93,
        "overtime_rate": 106.40,
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10573",
        "first_name": "Jeffrey",
        "last_name": "Gardiner",
        "union": "DC11",
        "regular_rate": 70.80,
        "overtime_rate": 106.20,
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10574",
        "first_name": "Hongpakasith",
        "last_name": "Saisomorn",
        "union": "DC11",
        "regular_rate": 52.72,
        "overtime_rate": 79.08,  # Calculated as 1.5x regular
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10491",
        "first_name": "Bruce",
        "last_name": "Dias",
        "union": "DC11",
        "regular_rate": 97.95,
        "overtime_rate": 146.93,
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10586",
        "first_name": "Joan",
        "last_name": "Pilarte",
        "union": "DC11",
        "regular_rate": 87.89,
        "overtime_rate": 131.84,
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10588",
        "first_name": "Corey",
        "last_name": "Glover",
        "union": "DC11",
        "regular_rate": 61.21,
        "overtime_rate": 91.82,  # Calculated as 1.5x regular (was #REF!)
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10582",
        "first_name": "Jhonathan",
        "last_name": "Giron",
        "union": "DC11",
        "regular_rate": 100.70,
        "overtime_rate": 151.05,  # Calculated as 1.5x regular (was #REF!)
        "health_welfare": 10.80,
        "pension": 13.90,
    },
    {
        "employee_number": "10595",
        "first_name": "Justin",
        "last_name": "Manchester",
        "union": "DC11",
        "regular_rate": 59.70,
        "overtime_rate": 89.55,  # Calculated as 1.5x regular (was #REF!)
        "health_welfare": 10.80,
        "pension": 13.90,
    },
]


def import_employees():
    db = get_session()

    print("=" * 70)
    print("Importing Employee Payroll Data")
    print("=" * 70)
    print()

    imported_count = 0
    updated_count = 0
    skipped_count = 0

    for emp_data in EMPLOYEES_DATA:
        emp_num = emp_data["employee_number"]

        # Check if employee already exists
        existing = (
            db.query(Employee).filter(Employee.employee_number == emp_num).first()
        )

        if existing:
            # Update existing employee
            existing.first_name = emp_data["first_name"]
            existing.last_name = emp_data["last_name"]
            existing.union = emp_data["union"]
            existing.regular_rate = Decimal(str(emp_data["regular_rate"]))
            existing.overtime_rate = Decimal(str(emp_data["overtime_rate"]))
            existing.health_welfare = Decimal(str(emp_data["health_welfare"]))
            existing.pension = Decimal(str(emp_data["pension"]))
            existing.active = True

            print(
                f"  🔄 Updated: {emp_data['first_name']} {emp_data['last_name']} (#{emp_num})"
            )
            updated_count += 1
        else:
            # Create new employee
            employee = Employee(
                employee_number=emp_data["employee_number"],
                first_name=emp_data["first_name"],
                last_name=emp_data["last_name"],
                union=emp_data["union"],
                regular_rate=Decimal(str(emp_data["regular_rate"])),
                overtime_rate=Decimal(str(emp_data["overtime_rate"])),
                health_welfare=Decimal(str(emp_data["health_welfare"])),
                pension=Decimal(str(emp_data["pension"])),
                active=True,
                notes=None,
            )
            db.add(employee)
            print(
                f"  ✅ Created: {emp_data['first_name']} {emp_data['last_name']} (#{emp_num}) - {emp_data['union']}"
            )
            imported_count += 1

    db.commit()

    print()
    print("=" * 70)
    print(f"Import Complete!")
    print(f"  New employees created: {imported_count}")
    print(f"  Existing employees updated: {updated_count}")
    print("=" * 70)
    print()

    # Show summary by union
    print("Employees by Union:")
    for union in ["DC9", "DC11", "DC35"]:
        employees = (
            db.query(Employee)
            .filter(Employee.union == union, Employee.active == True)
            .order_by(Employee.last_name)
            .all()
        )

        print(f"\n  {union}: {len(employees)} employees")
        for emp in employees:
            print(
                f"    [{emp.employee_number}] {emp.full_name} - "
                f"${emp.regular_rate}/hr (reg) / ${emp.overtime_rate}/hr (OT)"
            )

    db.close()


if __name__ == "__main__":
    import_employees()
