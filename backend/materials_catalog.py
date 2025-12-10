"""
TSI Materials Catalog - CLEAN VERSION (Duplicates Removed)
Based on provided price list - December 2024
Rule: Where duplicates exist, highest price is kept
"""

MATERIALS_CATALOG = {
    "EQUIPMENT": [
        {"name": "Ford F-250 Pickup Truck", "unit": "Day", "unit_price": 175.00},
        {"name": "Honda Generator", "unit": "Day", "unit_price": 62.00},
        {"name": "Power Washer", "unit": "Day", "unit_price": 72.00},
        {"name": "Hotel Room", "unit": "Day", "unit_price": 1.21},
    ],
    
    "MATERIALS": [
        {"name": "Epoxy mastic 2 gal kit", "unit": "Kit", "unit_price": 145.48},
        {"name": "Mek - 5 Gal", "unit": "Gallon", "unit_price": 19.85},
        {"name": "MEK Thinner 65 (Gal)", "unit": "Gallon", "unit_price": 34.13},
        {"name": "Macropxy 646 White (Gallon)", "unit": "Gallon", "unit_price": 82.46},
        {"name": "Macropxy 646 Black (Gallon)", "unit": "Gallon", "unit_price": 82.46},
        {"name": "Reducer 58 (Gallon)", "unit": "Gallon", "unit_price": 32.53},  # Kept higher price
    ],
    
    "PPE": [
        {"name": "Concentra- Blood lead", "unit": "Test", "unit_price": 136.00},
        {"name": "Coveralls/ Tyvek", "unit": "Each", "unit_price": 4.98},
        {"name": "Coveralls, Disposable XXL", "unit": "Each", "unit_price": 6.61},
        {"name": "Coveralls, Disposable XXXL", "unit": "Each", "unit_price": 7.40},
        {"name": "Double Eye Protection", "unit": "Each", "unit_price": 10.44},  # Kept higher price
        {"name": "Ear Plugs", "unit": "Each", "unit_price": 0.25},  # Kept higher price (note: one was "Pair", other "Each")
        {"name": "Gloves Blue & Yellow", "unit": "Pair", "unit_price": 6.15},
        {"name": "Gloves, Ansell Nylon Knit, Grey and White (Pair)", "unit": "Pair", "unit_price": 3.59},  # Kept higher price
        {"name": "Gloves, Latex/Nitrile", "unit": "Box", "unit_price": 24.06},  # Kept higher price
        {"name": "Head Socks", "unit": "Each", "unit_price": 1.20},  # Kept higher price
        {"name": "Organic Filter", "unit": "Each", "unit_price": 8.71},
        {"name": "P100 Dust Filter", "unit": "Each", "unit_price": 11.23},  # Kept higher price
        {"name": "Safety Glasses (Clear)", "unit": "Pair", "unit_price": 1.68},  # Kept higher price
        {"name": "Safety Glasses/ Tinted", "unit": "Pair", "unit_price": 1.42},
    ],
    
    "CONSUMABLES": [
        {"name": "AA Batteries - 10 pack", "unit": "Pack", "unit_price": 10.87},
        {"name": "AAA Batteries", "unit": "Each", "unit_price": 0.46},
        {"name": "Roller Naps 4\" (ea)", "unit": "Each", "unit_price": 14.18},  # Kept higher price
        {"name": "9 Piece Wire Brush Wheel set", "unit": "Set", "unit_price": 21.23},
        {"name": "Bent Rad 1\"", "unit": "Each", "unit_price": 1.00},
        {"name": "Bent Radiator Brushes1\" (ea)", "unit": "Each", "unit_price": 1.49},
        {"name": "Bent Radiator Brushes 2.5\" (ea)", "unit": "Each", "unit_price": 2.81},  # Kept higher price
        {"name": "Blue Painter's Tape", "unit": "Roll", "unit_price": 11.86},
        {"name": "Bristle Wheels", "unit": "Each", "unit_price": 46.63},  # Kept higher price
        {"name": "Bucket Liners (5 gal) (individual)", "unit": "Each", "unit_price": 3.81},  # Kept higher price
        {"name": "Bucket Liners (5 qt)", "unit": "Each", "unit_price": 1.42},  # Kept higher price
        {"name": "Coating Removal Discs", "unit": "Each", "unit_price": 17.04},  # Kept higher price
        {"name": "Cut Off Wheels", "unit": "Each", "unit_price": 3.20},
        {"name": "Disc Pad Holder 3m", "unit": "Each", "unit_price": 32.35},  # Kept higher price
        {"name": "Duct Tape (roll)", "unit": "Roll", "unit_price": 10.84},  # Kept higher price
        {"name": "Flapper Disc", "unit": "Each", "unit_price": 9.16},  # Kept higher price
        {"name": "Grinder Discs", "unit": "Each", "unit_price": 4.47},
        {"name": "Hand Pads/ Radnor", "unit": "Each", "unit_price": 1.82},
        {"name": "Hook n Loop 5\" sandpaper (box)", "unit": "Box", "unit_price": 43.75},
        {"name": "Ice", "unit": "Bag", "unit_price": 2.99},
        {"name": "Ice 20 lb", "unit": "Bag", "unit_price": 5.99},
        {"name": "Jex Needle Supports", "unit": "Each", "unit_price": 55.80},
        {"name": "Jex needles/ 50 pc", "unit": "Pack", "unit_price": 12.80},
        {"name": "Kresto Quickwipes", "unit": "Container", "unit_price": 44.54},  # Kept higher price
        {"name": "Poly- 6 Mil", "unit": "Roll", "unit_price": 127.00},
        {"name": "Project Source Paint Grid", "unit": "Each", "unit_price": 5.63},
        {"name": "Rags (box)", "unit": "Box", "unit_price": 63.05},  # Kept higher price
        {"name": "Salt Tests", "unit": "Test", "unit_price": 26.88},
        {"name": "Sandpaper (box)", "unit": "Box", "unit_price": 25.18},
        {"name": "Sani-wipes", "unit": "Pack", "unit_price": 11.10},  # Kept higher price
        {"name": "Spray Bottle", "unit": "Each", "unit_price": 4.98},
        {"name": "Testex Tape", "unit": "Roll", "unit_price": 1.25},
        {"name": "Trash bags (box)", "unit": "Box", "unit_price": 57.80},  # Kept higher price
        {"name": "Water", "unit": "Case", "unit_price": 12.19},  # Kept higher price
        {"name": "White Tape (4\" x 108' roll)", "unit": "Roll", "unit_price": 15.00},  # Kept higher price
        {"name": "Wire Cup Brush", "unit": "Each", "unit_price": 23.47},  # Kept higher price
    ],
    
    "FUEL": [
        {"name": "Diesel", "unit": "Gallon", "unit_price": 3.99},  # Kept higher price
        {"name": "Gas", "unit": "Gallon", "unit_price": 2.79},  # Kept higher price
        {"name": "Def Fluid- 1 Gal", "unit": "Gallon", "unit_price": 9.99},
        {"name": "Def Fluid 2.5 Gal", "unit": "Jug", "unit_price": 15.48},
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
    print("\n" + "="*60)
    print("MATERIALS CATALOG SUMMARY (CLEAN)")
    print("="*60)
    
    total_items = 0
    for category in ["EQUIPMENT", "MATERIALS", "PPE", "CONSUMABLES", "FUEL"]:
        items = MATERIALS_CATALOG.get(category, [])
        count = len(items)
        total_items += count
        print(f"\n{category}: {count} items")
        
        # Show all items in this clean version
        for item in items:
            print(f"  • {item['name']:<45} ${item['unit_price']:>7.2f} / {item['unit']}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL ITEMS: {total_items}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print_catalog_summary()