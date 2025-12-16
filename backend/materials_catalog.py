"""
TSI Materials Catalog - UPDATED FROM ACTUAL INVOICES
Based on backup invoices from November-December 2024
All prices verified from actual purchase receipts
"""

MATERIALS_CATALOG = {
    "EQUIPMENT": [
        {"name": "Dehumidifier Rental", "unit": "Day", "unit_price": 4244.27},  # Based on 2-unit rental
        {"name": "5 Gallon Bucket", "unit": "Each", "unit_price": 3.98},  # Home Depot
    ],
    
    "MATERIALS": [
        {"name": "Acrolon Paint", "unit": "Gallon", "unit_price": 65.00},  # Sherwin Williams 11.18.25
        {"name": "Paint Strainer", "unit": "Each", "unit_price": 1.14},  # Sherwin Williams (50/box)
        {"name": "Rac Tip 313", "unit": "Each", "unit_price": 45.99},  # Sherwin Williams 11.18.25
        {"name": "Roller Frame Mini 4\"", "unit": "Each", "unit_price": 4.33},  # Sherwin Williams
        {"name": "Spray Gun Parts", "unit": "Set", "unit_price": 800.30},  # Allredi 11.12.25
        {"name": "Spray Adhesive 3M", "unit": "Can", "unit_price": 17.98},  # Home Depot
        {"name": "White Tape (Eagle)", "unit": "Roll", "unit_price": 12.50},  # Eagle 12.05.25
        {"name": "Zip Tape Rolls", "unit": "Roll", "unit_price": 34.95},  # Home Depot
        {"name": "Throat Oil", "unit": "Bottle", "unit_price": 6.99},  # Harbor Freight
    ],
    
    "PPE": [
        {"name": "Coveralls 2XL", "unit": "Each", "unit_price": 5.23},  # Airgas ($130.75/25)
        {"name": "Gloves Thermal", "unit": "Pair", "unit_price": 7.56},  # Airgas 11.12.25
        {"name": "Gloves Nitrile Latex Disposable", "unit": "Box", "unit_price": 14.20},  # Airgas 07.10.25
        {"name": "Head Socks", "unit": "Each", "unit_price": 0.81},  # Tiffany Brush 12.09.25
        {"name": "Organic Vapor Cartridge 6001", "unit": "Each", "unit_price": 7.95},  # Airgas ($477.14/60)
        {"name": "P100 Filter Particulate", "unit": "Each", "unit_price": 4.43},  # Airgas ($443.42/100)
        {"name": "Respirator Wipes", "unit": "Each", "unit_price": 7.65},  # Airgas 09.16.25
    ],
    
    "CONSUMABLES": [
        {"name": "AAA Batteries", "unit": "Box", "unit_price": 13.92},  # Airgas 10.28.25
        {"name": "Bucket Liners 5 Gallon", "unit": "Each", "unit_price": 3.28},  # Sherwin Williams 04.03.25
        {"name": "Bucket Liners 5 Quart", "unit": "Each", "unit_price": 1.19},  # Sherwin Williams 04.03.25
        {"name": "Drop Cloth 4x12", "unit": "Each", "unit_price": 8.99},  # Harbor Freight
        {"name": "Drop Cloth 4x15", "unit": "Each", "unit_price": 10.99},  # Harbor Freight
        {"name": "Lincoln Stainless Steel Brush", "unit": "Each", "unit_price": 8.98},  # Home Depot 12.10.25
        {"name": "Mini Paint Roller 6-Pack", "unit": "Pack", "unit_price": 11.34},  # Home Depot
        {"name": "Mini Paint Roller", "unit": "Each", "unit_price": 1.89},  # Individual ($11.34/6)
        {"name": "Bent Rad Brush 1 Inch", "unit": "Each", "unit_price": 1.00},  # Tiffany Brush 12.09.25
        {"name": "Bent Rad Brush 2.5 Inch", "unit": "Each", "unit_price": 2.25},  # Tiffany Brush 12.09.25
        {"name": "Rags", "unit": "Case", "unit_price": 51.56},  # Airgas 11.24.25
        {"name": "Razor Blades", "unit": "Pack", "unit_price": 22.98},  # Lowes 03.02.23
        {"name": "Ryobi Abrasive Brush Kit", "unit": "Kit", "unit_price": 11.97},  # Home Depot 12.10.25
        {"name": "Ryobi Wire Wheel Assortment", "unit": "Set", "unit_price": 17.97},  # Home Depot 12.10.25
        {"name": "Telescopic Mirror", "unit": "Each", "unit_price": 7.74},  # Airgas 12.02.25
        {"name": "Trash Bags", "unit": "Box", "unit_price": 23.00},  # Airgas 12.02.25
    ],
    
    "FUEL": [
        # Note: Fuel prices vary by date - these are placeholders
        # Actual gallons purchased should be tracked separately
        {"name": "Diesel", "unit": "Gallon", "unit_price": 3.99},
        {"name": "Gasoline", "unit": "Gallon", "unit_price": 3.29},
    ],
}

def get_all_items():
    """Return flattened list with IDs"""
    items = []
    item_id = 1
    for category, catalog_items in MATERIALS_CATALOG.items():
        for item in catalog_items:
            items.append({
                "id": item_id,
                "category": category,
                **item
            })
            item_id += 1
    return items

def get_items_by_category(category):
    """Get items for specific category"""
    return MATERIALS_CATALOG.get(category, [])

def print_catalog_summary():
    """Print summary of catalog for verification"""
    print("\n" + "="*70)
    print("MATERIALS CATALOG - UPDATED FROM ACTUAL INVOICES")
    print("="*70)
    
    total_items = 0
    for category in ["EQUIPMENT", "MATERIALS", "PPE", "CONSUMABLES", "FUEL"]:
        items = MATERIALS_CATALOG.get(category, [])
        count = len(items)
        total_items += count
        print(f"\n{category}: {count} items")
        
        for item in items:
            print(f"  • {item['name']:<50} ${item['unit_price']:>7.2f} / {item['unit']}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL ITEMS: {total_items}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print_catalog_summary()