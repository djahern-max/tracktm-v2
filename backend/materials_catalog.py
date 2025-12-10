"""
TSI Materials Catalog - Updated with Actual Pricing
Based on provided price list - December 2024
"""

MATERIALS_CATALOG = {
    "EQUIPMENT": [
        {"name": "Ford F-250", "unit": "Day", "unit_price": 175.00},
        {"name": "Honda Generator", "unit": "Day", "unit_price": 62.00},
    ],
    
    "MATERIALS": [
        {"name": "Epoxy mastic 2 gal kit", "unit": "Kit", "unit_price": 145.48},
        {"name": "Mek - 5 Gal", "unit": "Gallon", "unit_price": 19.85},
        {"name": "Reducer #58 5 gal", "unit": "Gallon", "unit_price": 27.32},
    ],
    
    "PPE": [
        {"name": "Concentra- Blood lead", "unit": "Test", "unit_price": 136.00},
        {"name": "Coveralls/ Tyvek", "unit": "Each", "unit_price": 4.98},
        {"name": "Dbl eye face shield", "unit": "Each", "unit_price": 8.35},
        {"name": "Ear Plugs", "unit": "Pair", "unit_price": 0.18},
        {"name": "Gloves Blue & Yellow", "unit": "Pair", "unit_price": 6.15},
        {"name": "Gloves Gray & White", "unit": "Pair", "unit_price": 3.10},
        {"name": "Gloves Latex/ Nitrile", "unit": "Box", "unit_price": 14.20},
        {"name": "Head Socks", "unit": "Each", "unit_price": 0.81},
        {"name": "P100 filters", "unit": "Each", "unit_price": 8.87},
        {"name": "Safety Glasses/ Clear", "unit": "Pair", "unit_price": 1.42},
        {"name": "Safety Glasses/ Tinted", "unit": "Pair", "unit_price": 1.42},
    ],
    
    "CONSUMABLES": [
        {"name": "AA Batteries - 10 pack", "unit": "Pack", "unit_price": 10.87},
        {"name": "4\" roller naps", "unit": "Each", "unit_price": 9.64},
        {"name": "Bent Rad 1\"", "unit": "Each", "unit_price": 1.00},
        {"name": "Bent Rad Brushes 2 1/2", "unit": "Each", "unit_price": 2.25},
        {"name": "Bristle wheels", "unit": "Each", "unit_price": 36.15},
        {"name": "Bucket liners 5 gal", "unit": "Each", "unit_price": 3.28},
        {"name": "Bucket Liners 5 qt", "unit": "Each", "unit_price": 1.19},
        {"name": "Coating rem. Discs", "unit": "Each", "unit_price": 14.00},
        {"name": "Cut Off Wheels", "unit": "Each", "unit_price": 3.20},
        {"name": "Disc Pad Holder 3m", "unit": "Each", "unit_price": 32.35},
        {"name": "Duct Tape", "unit": "Roll", "unit_price": 8.67},
        {"name": "Flapper Discs", "unit": "Each", "unit_price": 8.04},
        {"name": "Grinder Discs", "unit": "Each", "unit_price": 4.47},
        {"name": "Hand Pads/ Radnor", "unit": "Each", "unit_price": 1.82},
        {"name": "Ice", "unit": "Bag", "unit_price": 2.99},
        {"name": "Ice 20 lb", "unit": "Bag", "unit_price": 5.99},
        {"name": "Jex Needle Supports", "unit": "Each", "unit_price": 55.80},
        {"name": "Jex needles/ 50 pc", "unit": "Pack", "unit_price": 12.80},
        {"name": "Kresto Quik Wipes", "unit": "Container", "unit_price": 31.93},
        {"name": "Poly- 6 Mil", "unit": "Roll", "unit_price": 127.00},
        {"name": "Rags", "unit": "Box", "unit_price": 51.56},
        {"name": "Sani Wipes", "unit": "Pack", "unit_price": 9.54},
        {"name": "Trash Bags", "unit": "Box", "unit_price": 32.01},
        {"name": "Water", "unit": "Case", "unit_price": 12.19},
        {"name": "White tape (4x108) roll", "unit": "Roll", "unit_price": 12.50},
        {"name": "Wire Cup Brushes-Home Depot", "unit": "Each", "unit_price": 23.47},
    ],
    
    "FUEL": [
        {"name": "Diesel", "unit": "Gallon", "unit_price": 3.49},
        {"name": "Gas", "unit": "Gallon", "unit_price": 2.19},
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
