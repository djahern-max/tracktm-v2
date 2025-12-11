"""
Labor Catalog - T&M Rates
Based on 2022 T&M and Equipment Rates contract
"""

LABOR_CATALOG = {
    "LABOR": [
        {
            "name": "Supervisor",
            "straight_rate": 141.41,
            "overtime_rate": 182.80,
            "unit": "Hour",
            "category": "LABOR"
        },
        {
            "name": "Painter", 
            "straight_rate": 139.41,
            "overtime_rate": 180.80,
            "unit": "Hour",
            "category": "LABOR"
        },
        {
            "name": "Project Manager",
            "straight_rate": 155.00,
            "overtime_rate": 155.00,  # Same rate for PM
            "unit": "Hour",
            "category": "LABOR"
        },
        {
            "name": "Per Diem",
            "straight_rate": 75.00,  # Typical per diem rate
            "overtime_rate": 0.00,   # No OT for per diem
            "unit": "Day",
            "category": "LABOR"
        },
    ]
}

# Night shift differential
NIGHT_SHIFT_DIFFERENTIAL = 2.00  # Add $2/hr for night shift

def get_all_labor_roles():
    """Return flattened list with IDs"""
    roles = []
    role_id = 1
    for category, catalog_items in LABOR_CATALOG.items():
        for item in catalog_items:
            roles.append({
                "id": role_id,
                **item
            })
            role_id += 1
    return roles

def get_labor_by_category(category):
    """Get labor roles for specific category"""
    return LABOR_CATALOG.get(category, [])

if __name__ == "__main__":
    print("Labor Roles:")
    print("=" * 60)
    for role in get_all_labor_roles():
        print(f"{role['name']:<20} ${role['straight_rate']:>7.2f}/hr (Reg)  ${role['overtime_rate']:>7.2f}/hr (OT)")
    print()
    print(f"Night Shift Differential: +${NIGHT_SHIFT_DIFFERENTIAL:.2f}/hr")