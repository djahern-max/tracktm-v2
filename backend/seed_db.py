"""
Seed the database with materials catalog
"""
from database import init_db, get_session, Material
from materials_catalog import get_all_items

def seed_materials():
    """Populate materials table from catalog"""
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Get session
    session = get_session()
    
    try:
        # Check if already seeded
        existing_count = session.query(Material).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} materials")
            response = input("Do you want to re-seed? This will clear existing data. (yes/no): ")
            if response.lower() != 'yes':
                print("Skipping seed.")
                return
            
            # Clear existing materials
            session.query(Material).delete()
            session.commit()
            print("🗑️  Cleared existing materials")
        
        # Get all items from catalog
        items = get_all_items()
        
        print(f"\n📦 Seeding {len(items)} materials...")
        
        # Insert materials
        for item in items:
            material = Material(
                name=item['name'],
                category=item['category'],
                unit=item['unit'],
                unit_price=item['unit_price']
            )
            session.add(material)
        
        session.commit()
        
        print(f"✅ Successfully seeded {len(items)} materials!")
        
        # Show summary by category
        print("\n📊 Materials by category:")
        for category in ['CONSUMABLES', 'MATERIALS', 'PPE', 'FUEL']:
            count = session.query(Material).filter(Material.category == category).count()
            print(f"   {category}: {count} items")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_materials()
