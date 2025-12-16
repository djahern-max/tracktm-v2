"""
TrackTM Simplified API
Single PDF output with markup logic
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal
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
    init_db,
)

from simplified_report_generator import generate_daily_report_pdf


# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✓ Database initialized")
    yield


app = FastAPI(title="TrackTM Simplified API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# PYDANTIC MODELS
# ============================================


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
    rate_period: str = "daily"
    unit_rate: Optional[float] = None


class DailyEntryInput(BaseModel):
    job_number: str
    entry_date: str
    line_items: List[LineItemInput]
    labor_items: Optional[List[LaborItemInput]] = []
    equipment_items: Optional[List[EquipmentRentalInput]] = []


class ReportRequest(BaseModel):
    job_number: str
    job_name: str
    company_name: str
    company_address_line1: str
    company_address_line2: str
    company_phone: str
    company_fax: Optional[str] = None
    start_date: Optional[str] = None


# ============================================
# DATABASE DEPENDENCY
# ============================================


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


# ============================================
# ROUTES
# ============================================


@app.get("/")
def root():
    return {
        "app": "TrackTM - Simplified",
        "version": "1.0.0",
        "description": "Daily timesheet with 10% OH + 10% Profit markup on materials and equipment",
    }


@app.get("/api/materials", response_model=List[MaterialResponse])
def get_materials(db: Session = Depends(get_db)):
    """Get all materials in category order"""
    CATEGORY_ORDER = ["EQUIPMENT", "MATERIALS", "PPE", "CONSUMABLES", "FUEL", "LODGING"]

    all_materials = db.query(Material).all()

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


@app.get("/api/equipment-rentals", response_model=List[EquipmentRentalResponse])
def get_equipment_rentals(
    year: str = "2022",
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

    return rentals


@app.get("/api/entries/{job_number}/{entry_date}")
def get_entry_by_date(job_number: str, entry_date: str, db: Session = Depends(get_db)):
    """Get a specific daily entry"""
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
    """Create or update a daily entry"""

    entry_date = datetime.strptime(entry_input.entry_date, "%Y-%m-%d").date()

    # Check if entry exists
    existing_entry = (
        db.query(DailyEntry)
        .filter(
            DailyEntry.job_number == entry_input.job_number,
            DailyEntry.entry_date == entry_date,
        )
        .first()
    )

    if existing_entry:
        daily_entry = existing_entry
        # Delete existing items
        db.query(EntryLineItem).filter(
            EntryLineItem.daily_entry_id == daily_entry.id
        ).delete()
        db.query(LaborEntry).filter(
            LaborEntry.daily_entry_id == daily_entry.id
        ).delete()
        db.query(EquipmentRentalEntry).filter(
            EquipmentRentalEntry.daily_entry_id == daily_entry.id
        ).delete()
    else:
        daily_entry = DailyEntry(
            job_number=entry_input.job_number, entry_date=entry_date
        )
        db.add(daily_entry)
        db.flush()

    # Add material line items
    for line_item_input in entry_input.line_items:
        if line_item_input.quantity > 0:
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

    # Add equipment rental items
    if entry_input.equipment_items:
        for equip_item in entry_input.equipment_items:
            if equip_item.quantity > 0:
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

                if equip_item.rate_period == "weekly":
                    rate = result[4]
                elif equip_item.rate_period == "monthly":
                    rate = result[5]
                else:
                    rate = result[3]

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

    # Add labor entries
    if entry_input.labor_items:
        for labor_item in entry_input.labor_items:
            if labor_item.regular_hours > 0 or labor_item.overtime_hours > 0:
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


@app.post("/api/reports/daily")
def generate_daily_report(request: ReportRequest, db: Session = Depends(get_db)):
    """Generate daily report PDF with markup"""

    try:
        entry_date = request.start_date if request.start_date else None

        if not entry_date:
            raise HTTPException(
                status_code=400, detail="Please provide a date (use start_date field)"
            )

        # Get the specific entry
        entry = (
            db.query(DailyEntry)
            .filter(
                DailyEntry.job_number == request.job_number,
                DailyEntry.entry_date == entry_date,
            )
            .first()
        )

        if not entry:
            raise HTTPException(
                status_code=404, detail=f"No entry found for {entry_date}"
            )

        # Prepare timesheet data
        timesheet_data = {
            "job_number": request.job_number,
            "entry_date": str(entry.entry_date),
            "job_name": request.job_name or "",
            "company_name": request.company_name,
            "company_address_line1": request.company_address_line1,
            "company_address_line2": request.company_address_line2,
            "company_phone": request.company_phone,
            "company_fax": request.company_fax,
        }

        # Prepare entry data
        entry_data = entry.to_dict()

        # Generate PDF
        pdf_buffer = generate_daily_report_pdf(
            timesheet_data, entry_data, save_backup=True
        )

        # Generate filename
        filename = f"TSI_Report_{request.job_number}_{entry_date}.pdf"

        # Return PDF
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )
