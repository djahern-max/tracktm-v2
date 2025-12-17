"""
TrackTM Simplified API
Single PDF output with markup logic
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
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
from invoice_generator import generate_invoice_pdf


# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“ Database initialized")
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


class InvoiceRequest(BaseModel):
    job_number: str
    job_name: str
    invoice_number: Optional[str] = None  # Added - frontend sends this
    purchase_order: Optional[str] = None
    payment_terms_days: int = 30
    remit_to_email: Optional[str] = None
    ship_to_location: str
    company_name: str = "Tri-State Painting, LLC (TSI)"
    company_address_line1: str = "612 West Main Street Unit 2"
    company_address_line2: str = "Tilton, NH 03276"
    company_phone: str = "(603) 286-7657"
    company_fax: str = "(603) 286-7882"
    bill_to_name: str
    bill_to_address_line1: str
    bill_to_address_line2: str
    contract_number: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    aggregation_method: Optional[str] = "category"  # Added - frontend sends this


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
    """Serve the main application HTML"""
    return FileResponse("index.html")


@app.get("/test")
def test_page():
    """Serve the invoice module test page"""
    return FileResponse("test_invoice_module.html")


@app.get("/debug")
def debug_page():
    """Serve the invoice debug page"""
    return FileResponse("invoice_debug.html")


# Serve static files directly
@app.get("/app.js")
def serve_app_js():
    return FileResponse("app.js", media_type="application/javascript")


@app.get("/invoice.js")
def serve_invoice_js():
    return FileResponse("invoice.js", media_type="application/javascript")


@app.get("/styles.css")
def serve_styles_css():
    return FileResponse("styles.css", media_type="text/css")


@app.get("/logo.png")
def serve_logo():
    return FileResponse("logo.png", media_type="image/png")


@app.get("/api/")
def api_root():
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


@app.get("/api/job-invoice-defaults/{job_number}")
def get_job_invoice_defaults(job_number: str):
    """Get default invoice settings for a job number"""
    from job_invoice_defaults import get_job_defaults

    defaults = get_job_defaults(job_number)
    return {"defaults": defaults}


@app.post("/api/invoice/generate")
def generate_invoice(request: InvoiceRequest, db: Session = Depends(get_db)):
    """Generate invoice PDF by aggregating multiple daily entries"""

    try:
        job_number = request.job_number
        start_date = request.start_date
        end_date = request.end_date

        # Build query for date range
        query = db.query(DailyEntry).filter(DailyEntry.job_number == job_number)

        if start_date:
            query = query.filter(DailyEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(DailyEntry.entry_date <= end_date)

        entries = query.order_by(DailyEntry.entry_date).all()

        if not entries:
            raise HTTPException(
                status_code=404,
                detail=f"No entries found for job {job_number}"
                + (f" between {start_date} and {end_date}" if start_date else ""),
            )

        # Aggregate entries - use category method (Materials, Labor, Equipment)
        line_items = _aggregate_by_category(entries)

        # Calculate period display
        period = ""
        if start_date and end_date:
            start_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_obj = datetime.strptime(end_date, "%Y-%m-%d")
            period = (
                f"{start_obj.strftime('%m/%d/%y')} - {end_obj.strftime('%m/%d/%y')}"
            )
        elif start_date:
            period = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%y")

        # Calculate due date
        invoice_date = datetime.now()
        due_date = invoice_date + timedelta(days=request.payment_terms_days)

        # Use provided invoice number or generate one
        invoice_num = (
            request.invoice_number
            if request.invoice_number
            else f"{job_number}-{invoice_date.strftime('%Y%m%d')}"
        )

        # Prepare invoice data
        invoice_data = {
            "invoice_number": invoice_num,
            "job_number": job_number,
            "job_name": request.job_name,
            "invoice_date": invoice_date.strftime("%m/%d/%y"),
            "due_date": due_date.strftime("%m/%d/%y"),
            "purchase_order": request.purchase_order or "",
            "period": period,
            "terms": f"Net {request.payment_terms_days}",
            "company_name": request.company_name,
            "company_phone": request.company_phone,
            "company_fax": request.company_fax,
            "bill_to_name": request.bill_to_name,
            "bill_to_address_line1": request.bill_to_address_line1,
            "bill_to_address_line2": request.bill_to_address_line2,
            "ship_to_location": request.ship_to_location,
            "contract_number": request.contract_number or "",
        }

        # Generate PDF
        pdf_buffer = generate_invoice_pdf(invoice_data, line_items, save_backup=True)

        # Generate filename
        filename = f"Invoice_{invoice_num}_{job_number}.pdf"

        # Return PDF
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating invoice: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to generate invoice: {str(e)}"
        )


def _aggregate_by_category(entries):
    """Aggregate all items by category (Materials, Labor, Equipment)"""
    line_items = []

    # Aggregate materials
    materials_base = 0.0

    for entry in entries:
        for item in entry.line_items:
            # Skip dehumidifier rentals (handled separately)
            if (
                "dehumidifier" in item.material.name.lower()
                and "rental" in item.material.name.lower()
            ):
                continue
            else:
                materials_base += item.total_amount

    if materials_base > 0:
        # Apply markup: base + 10% OH + 10% profit
        materials_oh = materials_base * 0.10
        materials_profit = materials_base * 0.10
        materials_total_with_markup = materials_base + materials_oh + materials_profit

        line_items.append(
            {
                "billing_item": "Lump Sum",
                "description": "Materials - T&M Work Performed (with 10% OH + 10% Profit)",
                "quantity": 1,
                "unit_price": materials_total_with_markup,
                "unit": "Ea",
                "amount": materials_total_with_markup,
            }
        )

    # Aggregate equipment
    equipment_base = 0.0
    dehumidifier_total = 0.0

    for entry in entries:
        for item in entry.equipment_rental_items:
            # Check for dehumidifier rental - separate line item, no markup
            if (
                "dehumidifier" in item.equipment_name.lower()
                and "rental" in item.equipment_name.lower()
            ):
                dehumidifier_total += item.total_amount
            else:
                equipment_base += item.total_amount

    if equipment_base > 0:
        # Apply markup: base + 10% OH + 10% profit
        equipment_oh = equipment_base * 0.10
        equipment_profit = equipment_base * 0.10
        equipment_total_with_markup = equipment_base + equipment_oh + equipment_profit

        line_items.append(
            {
                "billing_item": "Lump Sum",
                "description": "Equipment Rentals - T&M Work Performed (with 10% OH + 10% Profit)",
                "quantity": 1,
                "unit_price": equipment_total_with_markup,
                "unit": "Ea",
                "amount": equipment_total_with_markup,
            }
        )

    # Dehumidifier rental as separate pass-through line item
    if dehumidifier_total > 0:
        line_items.append(
            {
                "billing_item": "Lump Sum",
                "description": "Dehumidifier Rental - United Rentals Invoice #253422466-002 (Pass-through)",
                "quantity": 1,
                "unit_price": dehumidifier_total,
                "unit": "Ea",
                "amount": dehumidifier_total,
            }
        )

    # Aggregate labor (no markup)
    labor_total = 0.0
    for entry in entries:
        for item in entry.labor_entries:
            labor_total += item.total_amount

    if labor_total > 0:
        line_items.append(
            {
                "billing_item": "Lump Sum",
                "description": "Labor - T&M Work Performed",
                "quantity": 1,
                "unit_price": labor_total,
                "unit": "Ea",
                "amount": labor_total,
            }
        )

    # Aggregate pass-through expenses (no markup)
    passthrough_total = 0.0
    for entry in entries:
        for item in entry.passthrough_expenses:
            passthrough_total += item.amount

    if passthrough_total > 0:
        line_items.append(
            {
                "billing_item": "Lump Sum",
                "description": "Pass-Through Expenses - Vendor Invoices",
                "quantity": 1,
                "unit_price": passthrough_total,
                "unit": "Ea",
                "amount": passthrough_total,
            }
        )

    return line_items
