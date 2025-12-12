"""
TrackTM API - Daily Timesheet Entry System
Updated with Labor Tracking Support + Invoice Generation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from decimal import Decimal
import os
from fastapi.responses import StreamingResponse
from typing import Optional
from invoice_generator import generate_invoice_pdf
from contextlib import asynccontextmanager
from sqlalchemy import text


from database import (
    get_session,
    Material,
    LaborRole,
    DailyEntry,
    EntryLineItem,
    LaborEntry,
    EquipmentRentalEntry,
    PassThroughExpense,
    init_db,
)


# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("Ã¢Å“â€¦ Database initialized")
    yield


app = FastAPI(title="TrackTM API - Daily Timesheet Entry", lifespan=lifespan)

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


class EquipmentRentalInput(BaseModel):
    equipment_rental_id: int
    quantity: float
    rate_period: str = "daily"  # Add this line
    unit_rate: Optional[float] = None


class PassThroughExpenseInput(BaseModel):
    vendor_name: str
    vendor_invoice_number: Optional[str] = None
    description: str
    amount: float
    invoice_date: Optional[str] = None  # YYYY-MM-DD
    category: str = "Equipment Rental"
    billing_period_start: Optional[str] = None  # YYYY-MM-DD
    billing_period_end: Optional[str] = None  # YYYY-MM-DD
    notes: Optional[str] = None


class DailyEntryInput(BaseModel):
    job_number: str
    entry_date: str  # YYYY-MM-DD
    line_items: List[LineItemInput]
    labor_items: Optional[List[LaborItemInput]] = []
    equipment_items: Optional[List[EquipmentRentalInput]] = []
    passthrough_items: Optional[List[PassThroughExpenseInput]] = []


class DailyEntryResponse(BaseModel):
    id: int
    job_number: str
    entry_date: str
    line_items: List[dict]
    labor_entries: List[dict]
    total_amount: float


class InvoiceRequest(BaseModel):
    job_number: str
    job_name: str
    purchase_order: Optional[str] = None
    payment_terms_days: int = 30
    remit_to_email: Optional[str] = None
    ship_to_location: str
    company_name: str
    company_address_line1: str
    company_address_line2: str
    company_phone: str
    company_fax: Optional[str] = None
    bill_to_name: str
    bill_to_address_line1: str
    bill_to_address_line2: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# Pydantic Models for Equipment Rentals
class EquipmentRentalResponse(BaseModel):
    id: int
    category: str
    name: str
    unit: str
    daily_rate: Optional[float]
    weekly_rate: Optional[float]
    monthly_rate: Optional[float]
    year: str
    active: bool


# Dependency
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


# Routes


@app.get("/")
def root():
    return {
        "app": "TrackTM - Daily Timesheet Entry",
        "version": "2.2.0",
        "endpoints": {
            "materials": "/api/materials",
            "labor_roles": "/api/labor-roles",
            "daily_entries": "/api/entries",
            "entry_by_date": "/api/entries/{job_number}/{date}",
            "generate_invoice": "/api/invoice/generate",
        },
    }


CATEGORY_ORDER = ["EQUIPMENT", "MATERIALS", "PPE", "CONSUMABLES", "FUEL", "LODGING"]


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
    """Create or update a daily entry with materials, labor, and equipment rentals"""

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

        # Delete existing line items, labor entries, equipment rentals, and passthrough expenses
        db.query(EntryLineItem).filter(
            EntryLineItem.daily_entry_id == daily_entry.id
        ).delete()
        db.query(LaborEntry).filter(
            LaborEntry.daily_entry_id == daily_entry.id
        ).delete()
        db.query(EquipmentRentalEntry).filter(
            EquipmentRentalEntry.daily_entry_id == daily_entry.id
        ).delete()
        db.query(PassThroughExpense).filter(
            PassThroughExpense.daily_entry_id == daily_entry.id
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

    # Add equipment rental items (only for non-zero quantities)
    if entry_input.equipment_items:
        for equip_item in entry_input.equipment_items:
            if equip_item.quantity > 0:
                # Fetch equipment details from equipment_rental_rates table
                result = db.execute(
                    text(
                        """
                        SELECT name, category, unit, daily_rate, weekly_rate, monthly_rate
                        FROM equipment_rental_rates
                        WHERE id = :equipment_id
                    """
                    ),
                    {"equipment_id": equip_item.equipment_rental_id},
                ).fetchone()

                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Equipment rental ID {equip_item.equipment_rental_id} not found",
                    )

                equipment_name = result[0]
                equipment_category = result[1]
                unit = result[2]

                # Determine rate based on rate_period (default to daily)
                if equip_item.rate_period == "weekly":
                    rate = result[4]  # weekly_rate
                elif equip_item.rate_period == "monthly":
                    rate = result[5]  # monthly_rate
                else:
                    rate = result[3]  # daily_rate

                if rate is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No {equip_item.rate_period} rate available for {equipment_name}",
                    )

                equipment_entry = EquipmentRentalEntry(
                    daily_entry_id=daily_entry.id,
                    equipment_rental_id=equip_item.equipment_rental_id,
                    quantity=Decimal(str(equip_item.quantity)),
                    unit_rate=Decimal(str(rate)),
                    equipment_name=equipment_name,
                    equipment_category=equipment_category,
                    unit=unit,
                )
                db.add(equipment_entry)

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

    # Add pass-through expenses
    if entry_input.passthrough_items:
        for passthrough in entry_input.passthrough_items:
            # Parse dates if provided
            invoice_date = None
            if passthrough.invoice_date:
                invoice_date = datetime.strptime(
                    passthrough.invoice_date, "%Y-%m-%d"
                ).date()

            billing_start = None
            if passthrough.billing_period_start:
                billing_start = datetime.strptime(
                    passthrough.billing_period_start, "%Y-%m-%d"
                ).date()

            billing_end = None
            if passthrough.billing_period_end:
                billing_end = datetime.strptime(
                    passthrough.billing_period_end, "%Y-%m-%d"
                ).date()

            passthrough_entry = PassThroughExpense(
                daily_entry_id=daily_entry.id,
                vendor_name=passthrough.vendor_name,
                vendor_invoice_number=passthrough.vendor_invoice_number,
                description=passthrough.description,
                amount=Decimal(str(passthrough.amount)),
                invoice_date=invoice_date,
                category=passthrough.category,
                billing_period_start=billing_start,
                billing_period_end=billing_end,
                notes=passthrough.notes,
            )
            db.add(passthrough_entry)

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
        # Equipment rentals total
        equipment_total = sum(
            equip.total_amount for equip in entry.equipment_rental_items
        )
        # Labor total
        labor_total = sum(labor.total_amount for labor in entry.labor_entries)
        # Combined total
        entry_total = materials_total + equipment_total + labor_total
        grand_total += entry_total

        entries_summary.append(
            {
                "date": str(entry.entry_date),
                "item_count": len(entry.line_items),
                "equipment_count": len(entry.equipment_rental_items),
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


@app.post("/api/invoice/generate")
def generate_invoice(request: InvoiceRequest, db: Session = Depends(get_db)):
    """Generate invoice PDF for a job"""

    try:
        # Get all entries for the job
        query = db.query(DailyEntry).filter(DailyEntry.job_number == request.job_number)

        # Apply date range filters if provided
        if request.start_date:
            query = query.filter(DailyEntry.entry_date >= request.start_date)
        if request.end_date:
            query = query.filter(DailyEntry.entry_date <= request.end_date)

        entries = query.all()

        if not entries:
            raise HTTPException(status_code=404, detail="No entries found for this job")

        # Calculate totals
        labor_total = 0.0
        materials_total = 0.0
        equipment_total = 0.0
        passthrough_total = 0.0

        period_start = None
        period_end = None

        for entry in entries:
            # Track date range
            if period_start is None or entry.entry_date < period_start:
                period_start = entry.entry_date
            if period_end is None or entry.entry_date > period_end:
                period_end = entry.entry_date

            # Sum materials
            for item in entry.line_items:
                materials_total += item.total_amount

            # Sum equipment rentals
            for equip in entry.equipment_rental_items:
                equipment_total += equip.total_amount

            # Sum labor
            for labor in entry.labor_entries:
                labor_total += labor.total_amount

            # Sum pass-through expenses
            for expense in entry.passthrough_expenses:
                passthrough_total += float(expense.amount)

        # Prepare invoice data
        invoice_data = {
            "job_number": request.job_number,
            "job_name": request.job_name,
            "purchase_order": request.purchase_order,
            "payment_terms_days": request.payment_terms_days,
            "remit_to_email": request.remit_to_email,
            "ship_to_location": request.ship_to_location,
            "company_name": request.company_name,
            "company_address_line1": request.company_address_line1,
            "company_address_line2": request.company_address_line2,
            "company_phone": request.company_phone,
            "company_fax": request.company_fax,
            "bill_to_name": request.bill_to_name,
            "bill_to_address_line1": request.bill_to_address_line1,
            "bill_to_address_line2": request.bill_to_address_line2,
            "period_start": str(period_start) if period_start else None,
            "period_end": str(period_end) if period_end else None,
        }

        # Combine materials and equipment into a single total for invoice
        combined_materials_total = materials_total + equipment_total

        # Generate PDF with 3 line items (returns BytesIO buffer)
        pdf_buffer = generate_invoice_pdf(
            invoice_data, labor_total, combined_materials_total, passthrough_total
        )

        # Generate filename
        from datetime import datetime

        date_suffix = datetime.now().strftime("%m%d%y")
        filename = f"Invoice_{request.job_number}-{date_suffix}.pdf"

        # Return PDF as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating invoice: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate invoice: {str(e)}"
        )


@app.get("/api/equipment-rentals", response_model=List[EquipmentRentalResponse])
def get_equipment_rentals(
    year: str = "2022",
    category: Optional[str] = None,
    active: bool = True,
    db: Session = Depends(get_db),
):
    """Get all equipment rental rates"""
    query = db.execute(
        text(
            """
        SELECT id, category, name, unit, daily_rate, weekly_rate, monthly_rate, year, active
        FROM equipment_rental_rates
        WHERE year = :year AND active = :active
    """
        ),
        {"year": year, "active": 1 if active else 0},
    )

    rentals = []
    for row in query:
        rentals.append(
            {
                "id": row[0],
                "category": row[1],
                "name": row[2],
                "unit": row[3],
                "daily_rate": float(row[4]) if row[4] else None,
                "weekly_rate": float(row[5]) if row[5] else None,
                "monthly_rate": float(row[6]) if row[6] else None,
                "year": row[7],
                "active": bool(row[8]),
            }
        )

    if category:
        rentals = [r for r in rentals if r["category"] == category]

    return rentals


@app.get("/api/equipment-rentals/categories")
def get_equipment_categories(year: str = "2022", db: Session = Depends(get_db)):
    """Get list of equipment rental categories"""
    result = db.execute(
        text(
            """
        SELECT DISTINCT category
        FROM equipment_rental_rates
        WHERE year = :year AND active = 1
        ORDER BY category
    """
        ),
        {"year": year},
    )

    return {"categories": [row[0] for row in result]}
