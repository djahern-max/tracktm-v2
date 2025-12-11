"""
Seed Labor Roles into Database
"""
from database import init_db, get_session, LaborRole
from labor_catalog import get_all_labor_roles

def seed_labor_roles():
    """Populate labor_roles table from catalog"""
    
    # Initialize database (creates new tables if they don't exist)
    print("Initializing database...")
    init_db()
    
    # Get session
    session = get_session()
    
    try:
        # Check if already seeded
        existing_count = session.query(LaborRole).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} labor roles")
            response = input("Do you want to re-seed? This will clear existing data. (yes/no): ")
            if response.lower() != 'yes':
                print("Skipping seed.")
                return
            
            # Clear existing labor roles
            session.query(LaborRole).delete()
            session.commit()
            print("🗑️  Cleared existing labor roles")
        
        # Get all roles from catalog
        roles = get_all_labor_roles()
        
        print(f"\n📦 Seeding {len(roles)} labor roles...")
        
        # Insert labor roles
        for role in roles:
            labor_role = LaborRole(
                name=role['name'],
                category=role['category'],
                straight_rate=role['straight_rate'],
                overtime_rate=role['overtime_rate'],
                unit=role['unit']
            )
            session.add(labor_role)
        
        session.commit()
        
        print(f"✅ Successfully seeded {len(roles)} labor roles!")
        
        # Show summary
        print("\n📊 Labor roles in database:")
        for role in session.query(LaborRole).all():
            print(f"   {role.name}: ${role.straight_rate:.2f}/hr (Reg), ${role.overtime_rate:.2f}/hr (OT)")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_labor_roles()