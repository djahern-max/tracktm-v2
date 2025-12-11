"""
TrackTM API - Daily Timesheet Entry System
Updated with Labor Tracking Support
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from decimal import Decimal

from database import (
    get_session,
    Material,
    LaborRole,
    DailyEntry,
    EntryLineItem,
    LaborEntry,
    init_db,
)

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


class LaborRoleResponse(BaseModel):
    id: int
    name: str
    category: str
    straight_rate: float
    overtime_rate: float
    unit: str


class LineItemInput(BaseModel):
    material_id: int
    quantity: float
    unit_price: Optional[float] = None


class LaborItemInput(BaseModel):
    labor_role_id: int
    employee_name: Optional[str] = None
    regular_hours: float = 0
    overtime_hours: float = 0
    night_shift: bool = False


class DailyEntryInput(BaseModel):
    job_number: str
    entry_date: str  # YYYY-MM-DD
    line_items: List[LineItemInput]
    labor_items: Optional[List[LaborItemInput]] = []  # Add this!


class DailyEntryResponse(BaseModel):
    id: int
    job_number: str
    entry_date: str
    line_items: List[dict]
    labor_entries: List[dict]
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
        "version": "2.1.0",
        "endpoints": {
            "materials": "/api/materials",
            "labor_roles": "/api/labor-roles",
            "daily_entries": "/api/entries",
            "entry_by_date": "/api/entries/{job_number}/{date}",
        },
    }


CATEGORY_ORDER = ["EQUIPMENT", "MATERIALS", "PPE", "CONSUMABLES", "FUEL"]


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


@app.get("/api/labor-roles", response_model=List[LaborRoleResponse])
def get_labor_roles(db: Session = Depends(get_db)):
    """Get all labor roles"""
    roles = db.query(LaborRole).order_by(LaborRole.name).all()
    return [role.to_dict() for role in roles]


@app.get("/api/materials/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get list of material categories"""
    categories = db.query(Material.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}


@app.post("/api/materials/{material_id}/price")
def update_material_price(
    material_id: int, unit_price: float, db: Session = Depends(get_db)
):
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
        "new_price": unit_price,
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
    entry = (
        db.query(DailyEntry)
        .filter(
            DailyEntry.job_number == job_number, DailyEntry.entry_date == entry_date
        )
        .first()
    )

    if not entry:
        return {"entry": None}

    return {"entry": entry.to_dict()}


@app.post("/api/entries")
def create_or_update_entry(entry_input: DailyEntryInput, db: Session = Depends(get_db)):
    """Create or update a daily entry with materials and labor"""

    # Parse date string to date object
    entry_date = datetime.strptime(entry_input.entry_date, "%Y-%m-%d").date()

    # Check if entry already exists
    existing_entry = (
        db.query(DailyEntry)
        .filter(
            DailyEntry.job_number == entry_input.job_number,
            DailyEntry.entry_date == entry_date,
        )
        .first()
    )

    if existing_entry:
        # Update existing entry
        daily_entry = existing_entry

        # Delete existing line items and labor entries
        db.query(EntryLineItem).filter(
            EntryLineItem.daily_entry_id == daily_entry.id
        ).delete()
        db.query(LaborEntry).filter(
            LaborEntry.daily_entry_id == daily_entry.id
        ).delete()
    else:
        # Create new entry
        daily_entry = DailyEntry(
            job_number=entry_input.job_number, entry_date=entry_date
        )
        db.add(daily_entry)
        db.flush()  # Get the ID

    # Add material line items (only for non-zero quantities)
    for line_item_input in entry_input.line_items:
        if line_item_input.quantity > 0:
            # Get material to get default price
            material = (
                db.query(Material)
                .filter(Material.id == line_item_input.material_id)
                .first()
            )

            if not material:
                raise HTTPException(
                    status_code=404,
                    detail=f"Material ID {line_item_input.material_id} not found",
                )

            # Use provided price or default from material
            unit_price = (
                line_item_input.unit_price
                if line_item_input.unit_price
                else material.unit_price
            )

            line_item = EntryLineItem(
                daily_entry_id=daily_entry.id,
                material_id=line_item_input.material_id,
                quantity=Decimal(str(line_item_input.quantity)),
                unit_price=Decimal(str(unit_price)),
            )
            db.add(line_item)

    # Add labor entries (only for non-zero hours)
    if entry_input.labor_items:
        for labor_item in entry_input.labor_items:
            if labor_item.regular_hours > 0 or labor_item.overtime_hours > 0:
                # Get labor role to validate
                labor_role = (
                    db.query(LaborRole)
                    .filter(LaborRole.id == labor_item.labor_role_id)
                    .first()
                )

                if not labor_role:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Labor role ID {labor_item.labor_role_id} not found",
                    )

                labor_entry = LaborEntry(
                    daily_entry_id=daily_entry.id,
                    labor_role_id=labor_item.labor_role_id,
                    employee_name=labor_item.employee_name,
                    regular_hours=Decimal(str(labor_item.regular_hours)),
                    overtime_hours=Decimal(str(labor_item.overtime_hours)),
                    night_shift=labor_item.night_shift,
                )
                db.add(labor_entry)

    db.commit()
    db.refresh(daily_entry)

    return {"message": "Entry saved successfully", "entry": daily_entry.to_dict()}


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
    entries = db.query(DailyEntry).filter(DailyEntry.job_number == job_number).all()

    if not entries:
        return {"summary": None}

    # Calculate totals
    total_days = len(entries)
    grand_total = 0

    entries_summary = []
    for entry in entries:
        # Materials total
        materials_total = sum(item.total_amount for item in entry.line_items)
        # Labor total
        labor_total = sum(labor.total_amount for labor in entry.labor_entries)
        # Combined total
        entry_total = materials_total + labor_total
        grand_total += entry_total

        entries_summary.append(
            {
                "date": str(entry.entry_date),
                "item_count": len(entry.line_items),
                "labor_count": len(entry.labor_entries),
                "total": entry_total,
            }
        )

    return {
        "summary": {
            "job_number": job_number,
            "total_days": total_days,
            "grand_total": grand_total,
            "entries": sorted(entries_summary, key=lambda x: x["date"]),
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
