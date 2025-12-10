"""
TrackTM API - Daily Timesheet Entry System
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date as date_type
from sqlalchemy.orm import Session
from decimal import Decimal

from database import get_session, Material, DailyEntry, EntryLineItem, init_db

app = FastAPI(title="TrackTM API - Daily Timesheet Entry")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class MaterialResponse(BaseModel):
    id: int
    name: str
    category: str
    unit: str
    unit_price: float

class LineItemInput(BaseModel):
    material_id: int
    quantity: float
    unit_price: Optional[float] = None

class DailyEntryInput(BaseModel):
    job_number: str
    entry_date: str  # YYYY-MM-DD
    line_items: List[LineItemInput]

class DailyEntryResponse(BaseModel):
    id: int
    job_number: str
    entry_date: str
    line_items: List[dict]
    total_amount: float

# Dependency
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database initialized")

# Routes

@app.get("/")
def root():
    return {
        "app": "TrackTM - Daily Timesheet Entry",
        "version": "2.0.0",
        "endpoints": {
            "materials": "/api/materials",
            "daily_entries": "/api/entries",
            "entry_by_date": "/api/entries/{job_number}/{date}"
        }
    }

CATEGORY_ORDER = ['EQUIPMENT', 'MATERIALS', 'PPE', 'CONSUMABLES', 'FUEL']

# Then replace the get_materials function:
@app.get("/api/materials", response_model=List[MaterialResponse])
def get_materials(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all materials in the correct category order"""
    query = db.query(Material)
    
    if category:
        query = query.filter(Material.category == category)
        materials = query.order_by(Material.name).all()
    else:
        # Get all materials and sort by custom category order
        all_materials = query.all()
        
        # Sort by category order, then by name within category
        def sort_key(mat):
            try:
                cat_index = CATEGORY_ORDER.index(mat.category)
            except ValueError:
                cat_index = 999
            return (cat_index, mat.name)
        
        materials = sorted(all_materials, key=sort_key)
    
    return [mat.to_dict() for mat in materials]

@app.get("/api/materials/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get list of material categories"""
    categories = db.query(Material.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}

@app.post("/api/materials/{material_id}/price")
def update_material_price(material_id: int, unit_price: float, db: Session = Depends(get_db)):
    """Update a material's unit price"""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    old_price = float(material.unit_price)
    material.unit_price = Decimal(str(unit_price))
    db.commit()
    
    return {
        "message": "Price updated",
        "material": material.name,
        "old_price": old_price,
        "new_price": unit_price
    }

@app.get("/api/entries")
def get_all_entries(job_number: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all daily entries, optionally filtered by job number"""
    query = db.query(DailyEntry)
    
    if job_number:
        query = query.filter(DailyEntry.job_number == job_number)
    
    entries = query.order_by(DailyEntry.entry_date.desc()).all()
    return {"entries": [entry.to_dict() for entry in entries]}

@app.get("/api/entries/{job_number}/{entry_date}")
def get_entry_by_date(job_number: str, entry_date: str, db: Session = Depends(get_db)):
    """Get a specific daily entry by job number and date"""
    entry = db.query(DailyEntry).filter(
        DailyEntry.job_number == job_number,
        DailyEntry.entry_date == entry_date
    ).first()
    
    if not entry:
        return {"entry": None}
    
    return {"entry": entry.to_dict()}

@app.post("/api/entries")
def create_or_update_entry(entry_input: DailyEntryInput, db: Session = Depends(get_db)):
    """Create or update a daily entry"""
    
    # Check if entry already exists
    existing_entry = db.query(DailyEntry).filter(
        DailyEntry.job_number == entry_input.job_number,
        DailyEntry.entry_date == entry_input.entry_date
    ).first()
    
    if existing_entry:
        # Update existing entry
        daily_entry = existing_entry
        
        # Delete existing line items
        db.query(EntryLineItem).filter(
            EntryLineItem.daily_entry_id == daily_entry.id
        ).delete()
    else:
        # Create new entry
        daily_entry = DailyEntry(
            job_number=entry_input.job_number,
            entry_date=entry_input.entry_date
        )
        db.add(daily_entry)
        db.flush()  # Get the ID
    
    # Add line items (only for non-zero quantities)
    for line_item_input in entry_input.line_items:
        if line_item_input.quantity > 0:
            # Get material to get default price
            material = db.query(Material).filter(
                Material.id == line_item_input.material_id
            ).first()
            
            if not material:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Material ID {line_item_input.material_id} not found"
                )
            
            # Use provided price or default from material
            unit_price = line_item_input.unit_price if line_item_input.unit_price else material.unit_price
            
            line_item = EntryLineItem(
                daily_entry_id=daily_entry.id,
                material_id=line_item_input.material_id,
                quantity=Decimal(str(line_item_input.quantity)),
                unit_price=Decimal(str(unit_price))
            )
            db.add(line_item)
    
    db.commit()
    db.refresh(daily_entry)
    
    return {
        "message": "Entry saved successfully",
        "entry": daily_entry.to_dict()
    }

@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete a daily entry"""
    entry = db.query(DailyEntry).filter(DailyEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(entry)
    db.commit()
    
    return {"message": "Entry deleted successfully"}

@app.get("/api/entries/{job_number}/summary")
def get_job_summary(job_number: str, db: Session = Depends(get_db)):
    """Get summary of all entries for a job"""
    entries = db.query(DailyEntry).filter(
        DailyEntry.job_number == job_number
    ).all()
    
    if not entries:
        return {"summary": None}
    
    # Calculate totals
    total_days = len(entries)
    grand_total = 0
    
    entries_summary = []
    for entry in entries:
        entry_total = sum(item.total_amount for item in entry.line_items)
        grand_total += entry_total
        entries_summary.append({
            "date": str(entry.entry_date),
            "item_count": len(entry.line_items),
            "total": entry_total
        })
    
    return {
        "summary": {
            "job_number": job_number,
            "total_days": total_days,
            "grand_total": grand_total,
            "entries": sorted(entries_summary, key=lambda x: x['date'])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
