"""
Simplified Daily Report Generator with Markup Logic
- 10% OH + 10% Profit on Materials (except Dehumidifier Rental)
- 10% OH + 10% Profit on Equipment (except Dehumidifier Rental)
- No markup on Labor
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from datetime import datetime
from io import BytesIO
import os


class TSIReportGenerator:
    """Simplified TSI report generator with proper markup"""

    # TSI Brand Colors
    TSI_BROWN = colors.HexColor("#8B6F47")
    TSI_DARK_BROWN = colors.HexColor("#6B5637")
    GRAY_DARK = colors.HexColor("#1f2937")
    GRAY_LIGHT = colors.HexColor("#f3f4f6")

    def __init__(self, logo_path=None):
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()
        self.logo_path = logo_path or "logo.png"
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup TSI-branded styles"""
        self.styles.add(
            ParagraphStyle(
                name="CompanyName",
                parent=self.styles["Normal"],
                fontSize=16,
                textColor=self.TSI_BROWN,
                fontName="Helvetica-Bold",
                spaceAfter=2,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Normal"],
                fontSize=18,
                textColor=self.TSI_BROWN,
                alignment=TA_RIGHT,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=self.TSI_DARK_BROWN,
                fontName="Helvetica-Bold",
                spaceAfter=6,
                spaceBefore=10,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SmallText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=self.GRAY_DARK,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="TableText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=self.GRAY_DARK,
            )
        )

    def generate_report(self, timesheet_data, entry_data, save_backup=True):
        """Generate daily report PDF with markup"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Header
        story.extend(self._create_header(timesheet_data))
        story.append(Spacer(1, 0.15 * inch))
        story.append(self._create_line())
        story.append(Spacer(1, 0.15 * inch))

        # Job info
        story.extend(self._create_job_info(timesheet_data))
        story.append(Spacer(1, 0.2 * inch))

        # Calculate totals with markup
        totals = self._calculate_totals_with_markup(entry_data)

        # Materials section
        if entry_data.get("line_items"):
            story.append(Paragraph("MATERIALS", self.styles["SectionHeader"]))
            materials_table, materials_subtotal = self._create_materials_table(
                entry_data["line_items"]
            )
            story.append(materials_table)
            story.append(Spacer(1, 0.1 * inch))

            # Show markup calculation
            markup_table = self._create_markup_table(
                "MATERIALS",
                totals["materials_base"],
                totals["materials_oh"],
                totals["materials_profit"],
                totals["materials_total"],
            )
            story.append(markup_table)
            story.append(Spacer(1, 0.15 * inch))

        # Equipment section
        if entry_data.get("equipment_rental_items"):
            story.append(Paragraph("EQUIPMENT RENTALS", self.styles["SectionHeader"]))
            equipment_table, equipment_subtotal = self._create_equipment_table(
                entry_data["equipment_rental_items"]
            )
            story.append(equipment_table)
            story.append(Spacer(1, 0.1 * inch))

            # Show markup calculation
            markup_table = self._create_markup_table(
                "EQUIPMENT",
                totals["equipment_base"],
                totals["equipment_oh"],
                totals["equipment_profit"],
                totals["equipment_total"],
            )
            story.append(markup_table)
            story.append(Spacer(1, 0.15 * inch))

        # Labor section (no markup)
        if entry_data.get("labor_entries"):
            story.append(Paragraph("LABOR", self.styles["SectionHeader"]))
            labor_table = self._create_labor_table(entry_data["labor_entries"])
            story.append(labor_table)
            story.append(Spacer(1, 0.15 * inch))

        # Grand total
        story.append(self._create_line())
        story.append(Spacer(1, 0.1 * inch))
        story.append(self._create_total_section(totals["grand_total"]))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        if save_backup:
            self._save_backup_pdf(buffer, timesheet_data)
            buffer.seek(0)

        return buffer

    def _is_dehumidifier_rental(self, item_name):
        """Check if item is Dehumidifier Rental (no markup)"""
        return "dehumidifier" in item_name.lower() and "rental" in item_name.lower()

    def _calculate_totals_with_markup(self, entry_data):
        """Calculate totals with markup, excluding Dehumidifier Rental"""
        materials_base = 0.0
        materials_base_no_markup = 0.0

        equipment_base = 0.0
        equipment_base_no_markup = 0.0

        labor_total = 0.0

        # Materials
        for item in entry_data.get("line_items", []):
            if self._is_dehumidifier_rental(item["material_name"]):
                materials_base_no_markup += item["total_amount"]
            else:
                materials_base += item["total_amount"]

        # Equipment
        for item in entry_data.get("equipment_rental_items", []):
            if self._is_dehumidifier_rental(item["equipment_name"]):
                equipment_base_no_markup += item["total_amount"]
            else:
                equipment_base += item["total_amount"]

        # Labor
        for item in entry_data.get("labor_entries", []):
            labor_total += item["total_amount"]

        # Calculate markups
        materials_oh = materials_base * 0.10
        materials_profit = materials_base * 0.10
        materials_total = (
            materials_base + materials_oh + materials_profit + materials_base_no_markup
        )

        equipment_oh = equipment_base * 0.10
        equipment_profit = equipment_base * 0.10
        equipment_total = (
            equipment_base + equipment_oh + equipment_profit + equipment_base_no_markup
        )

        grand_total = materials_total + equipment_total + labor_total

        return {
            "materials_base": materials_base,
            "materials_base_no_markup": materials_base_no_markup,
            "materials_oh": materials_oh,
            "materials_profit": materials_profit,
            "materials_total": materials_total,
            "equipment_base": equipment_base,
            "equipment_base_no_markup": equipment_base_no_markup,
            "equipment_oh": equipment_oh,
            "equipment_profit": equipment_profit,
            "equipment_total": equipment_total,
            "labor_total": labor_total,
            "grand_total": grand_total,
        }

    def _save_backup_pdf(self, buffer, timesheet_data):
        """Save a backup copy"""
        try:
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)

            job_number = timesheet_data["job_number"]
            date = timesheet_data["entry_date"]
            filename = f"TSI_Report_{job_number}_{date}.pdf"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, "wb") as f:
                f.write(buffer.getvalue())

            print(f"âœ“ Report saved: {filepath}")
        except Exception as e:
            print(f"Warning: Could not save report backup: {e}")

    def _create_line(self):
        """Create separator line"""
        line_data = [["", ""]]
        line_table = Table(line_data, colWidths=[7 * inch])
        line_table.setStyle(
            TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1.5, self.TSI_BROWN)])
        )
        return line_table

    def _create_header(self, data):
        """Create header with logo"""
        elements = []

        logo_element = None
        if os.path.exists(self.logo_path):
            try:
                logo = Image(
                    self.logo_path,
                    width=1.5 * inch,
                    height=0.8 * inch,
                    kind="proportional",
                )
                logo_element = logo
            except:
                pass

        if logo_element:
            header_data = [
                [
                    logo_element,
                    Paragraph(data["company_name"], self.styles["CompanyName"]),
                    Paragraph("DAILY REPORT", self.styles["ReportTitle"]),
                ]
            ]
            header_table = Table(
                header_data, colWidths=[1.5 * inch, 3.25 * inch, 2.25 * inch]
            )
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "LEFT"),
                        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ]
                )
            )
        else:
            header_data = [
                [
                    Paragraph(data["company_name"], self.styles["CompanyName"]),
                    Paragraph("DAILY REPORT", self.styles["ReportTitle"]),
                ]
            ]
            header_table = Table(header_data, colWidths=[4 * inch, 3 * inch])
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ]
                )
            )

        elements.append(header_table)

        contact_info = (
            f"{data['company_address_line1']}<br/>{data['company_address_line2']}<br/>"
        )
        contact_info += f"Phone: {data['company_phone']}"
        if data.get("company_fax"):
            contact_info += f" | Fax: {data['company_fax']}"

        contact_para = Paragraph(contact_info, self.styles["SmallText"])
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(contact_para)

        return elements

    def _create_job_info(self, data):
        """Create job information section"""
        elements = []

        try:
            date_obj = datetime.strptime(data["entry_date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
        except:
            formatted_date = data["entry_date"]

        metadata_rows = [
            [
                Paragraph("<b>Job Number:</b>", self.styles["SmallText"]),
                Paragraph(data["job_number"], self.styles["SmallText"]),
                Paragraph("<b>Date:</b>", self.styles["SmallText"]),
                Paragraph(formatted_date, self.styles["SmallText"]),
            ],
        ]

        if data.get("job_name"):
            metadata_rows.append(
                [
                    Paragraph("<b>Job Name:</b>", self.styles["SmallText"]),
                    Paragraph(data["job_name"], self.styles["SmallText"]),
                    "",
                    "",
                ]
            )

        metadata_table = Table(
            metadata_rows, colWidths=[1.2 * inch, 2.3 * inch, 0.8 * inch, 2.7 * inch]
        )
        metadata_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (2, -1), "LEFT"),
                    ("ALIGN", (3, 0), (3, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        elements.append(metadata_table)
        return elements

    def _create_materials_table(self, line_items):
        """Create materials table"""
        table_data = [
            [
                Paragraph("<b>Material</b>", self.styles["TableText"]),
                Paragraph("<b>Unit</b>", self.styles["TableText"]),
                Paragraph("<b>Quantity</b>", self.styles["TableText"]),
                Paragraph("<b>Price</b>", self.styles["TableText"]),
                Paragraph("<b>Total</b>", self.styles["TableText"]),
            ]
        ]

        materials_total = 0
        for item in line_items:
            qty = (
                f"{item['quantity']:.1f}"
                if item["quantity"] % 1 != 0
                else f"{int(item['quantity'])}"
            )

            # Add markup indicator for Dehumidifier Rental
            name = item["material_name"]
            if self._is_dehumidifier_rental(name):
                name += " *"

            table_data.append(
                [
                    Paragraph(name, self.styles["TableText"]),
                    Paragraph(item["unit"], self.styles["TableText"]),
                    Paragraph(qty, self.styles["TableText"]),
                    Paragraph(f"${item['unit_price']:.2f}", self.styles["TableText"]),
                    Paragraph(f"${item['total_amount']:.2f}", self.styles["TableText"]),
                ]
            )
            materials_total += item["total_amount"]

        # Subtotal row
        table_data.append(
            [
                Paragraph("<b>MATERIALS SUBTOTAL</b>", self.styles["TableText"]),
                "",
                "",
                "",
                Paragraph(f"<b>${materials_total:,.2f}</b>", self.styles["TableText"]),
            ]
        )

        table = Table(
            table_data,
            colWidths=[2.8 * inch, 0.8 * inch, 1 * inch, 1 * inch, 1.4 * inch],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.GRAY_LIGHT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.TSI_DARK_BROWN),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -2), 9),
                    ("TOPPADDING", (0, 1), (-1, -2), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -2), 6),
                    ("BACKGROUND", (0, -1), (-1, -1), self.GRAY_LIGHT),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (3, -1), "CENTER"),
                    ("ALIGN", (4, 0), (4, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, self.TSI_BROWN),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#e5e7eb")),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, self.TSI_BROWN),
                    ("BOX", (0, 0), (-1, -1), 1, self.TSI_BROWN),
                ]
            )
        )

        return table, materials_total

    def _create_equipment_table(self, equipment_items):
        """Create equipment table"""
        table_data = [
            [
                Paragraph("<b>Equipment</b>", self.styles["TableText"]),
                Paragraph("<b>Unit</b>", self.styles["TableText"]),
                Paragraph("<b>Quantity</b>", self.styles["TableText"]),
                Paragraph("<b>Rate</b>", self.styles["TableText"]),
                Paragraph("<b>Total</b>", self.styles["TableText"]),
            ]
        ]

        equipment_total = 0
        for item in equipment_items:
            qty = (
                f"{item['quantity']:.1f}"
                if item["quantity"] % 1 != 0
                else f"{int(item['quantity'])}"
            )

            # Add markup indicator for Dehumidifier Rental
            name = item["equipment_name"]
            if self._is_dehumidifier_rental(name):
                name += " *"

            table_data.append(
                [
                    Paragraph(name, self.styles["TableText"]),
                    Paragraph(item["unit"], self.styles["TableText"]),
                    Paragraph(qty, self.styles["TableText"]),
                    Paragraph(f"${item['unit_rate']:.2f}", self.styles["TableText"]),
                    Paragraph(f"${item['total_amount']:.2f}", self.styles["TableText"]),
                ]
            )
            equipment_total += item["total_amount"]

        # Subtotal row
        table_data.append(
            [
                Paragraph("<b>EQUIPMENT SUBTOTAL</b>", self.styles["TableText"]),
                "",
                "",
                "",
                Paragraph(f"<b>${equipment_total:,.2f}</b>", self.styles["TableText"]),
            ]
        )

        table = Table(
            table_data,
            colWidths=[2.8 * inch, 0.8 * inch, 1 * inch, 1 * inch, 1.4 * inch],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.GRAY_LIGHT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.TSI_DARK_BROWN),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -2), 9),
                    ("TOPPADDING", (0, 1), (-1, -2), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -2), 6),
                    ("BACKGROUND", (0, -1), (-1, -1), self.GRAY_LIGHT),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (3, -1), "CENTER"),
                    ("ALIGN", (4, 0), (4, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, self.TSI_BROWN),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#e5e7eb")),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, self.TSI_BROWN),
                    ("BOX", (0, 0), (-1, -1), 1, self.TSI_BROWN),
                ]
            )
        )

        return table, equipment_total

    def _create_labor_table(self, labor_entries):
        """Create labor table"""
        table_data = [
            [
                Paragraph("<b>Employee</b>", self.styles["TableText"]),
                Paragraph("<b>Role</b>", self.styles["TableText"]),
                Paragraph("<b>Reg Hrs</b>", self.styles["TableText"]),
                Paragraph("<b>OT Hrs</b>", self.styles["TableText"]),
                Paragraph("<b>Night</b>", self.styles["TableText"]),
                Paragraph("<b>Total</b>", self.styles["TableText"]),
            ]
        ]

        labor_total = 0
        for entry in labor_entries:
            employee_name = entry.get("employee_name") or "â€”"
            reg_hrs = (
                f"{entry['regular_hours']:.1f}"
                if entry["regular_hours"] % 1 != 0
                else f"{int(entry['regular_hours'])}"
            )
            ot_hrs = (
                f"{entry['overtime_hours']:.1f}"
                if entry["overtime_hours"] % 1 != 0
                else f"{int(entry['overtime_hours'])}"
            )
            night_shift = "Yes" if entry.get("night_shift") else "No"

            table_data.append(
                [
                    Paragraph(employee_name, self.styles["TableText"]),
                    Paragraph(entry["role_name"], self.styles["TableText"]),
                    Paragraph(reg_hrs, self.styles["TableText"]),
                    Paragraph(ot_hrs, self.styles["TableText"]),
                    Paragraph(night_shift, self.styles["TableText"]),
                    Paragraph(
                        f"${entry['total_amount']:,.2f}", self.styles["TableText"]
                    ),
                ]
            )
            labor_total += entry["total_amount"]

        # Subtotal row
        table_data.append(
            [
                Paragraph("<b>LABOR TOTAL</b>", self.styles["TableText"]),
                "",
                "",
                "",
                "",
                Paragraph(f"<b>${labor_total:,.2f}</b>", self.styles["TableText"]),
            ]
        )

        table = Table(
            table_data,
            colWidths=[
                1.8 * inch,
                1.5 * inch,
                0.8 * inch,
                0.8 * inch,
                0.6 * inch,
                1 * inch,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.GRAY_LIGHT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.TSI_DARK_BROWN),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -2), 9),
                    ("TOPPADDING", (0, 1), (-1, -2), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -2), 6),
                    ("BACKGROUND", (0, -1), (-1, -1), self.GRAY_LIGHT),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (4, -1), "CENTER"),
                    ("ALIGN", (5, 0), (5, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, self.TSI_BROWN),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#e5e7eb")),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, self.TSI_BROWN),
                    ("BOX", (0, 0), (-1, -1), 1, self.TSI_BROWN),
                ]
            )
        )

        return table

    def _create_markup_table(self, category, base, oh, profit, total):
        """Create markup calculation table"""
        data = [
            [f"{category} Base:", f"${base:,.2f}"],
            ["10% Overhead:", f"${oh:,.2f}"],
            ["10% Profit:", f"${profit:,.2f}"],
            [f"{category} TOTAL:", f"${total:,.2f}"],
        ]

        # Add note about Dehumidifier Rental if applicable
        if base < total - oh - profit:
            data.insert(
                1,
                [
                    "* Dehumidifier Rental (no markup):",
                    f"${(total - oh - profit - base):,.2f}",
                ],
            )

        table = Table(data, colWidths=[5.8 * inch, 1.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),  # This makes the last row bold
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, self.TSI_BROWN),
                ]
            )
        )
        return table

    def _create_total_section(self, grand_total):
        """Create grand total section"""
        total_data = [
            [
                Paragraph("<b>GRAND TOTAL:</b>", self.styles["Normal"]),
                Paragraph(f"<b>${grand_total:,.2f}</b>", self.styles["Normal"]),
            ]
        ]

        total_table = Table(total_data, colWidths=[5.6 * inch, 1.4 * inch])
        total_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 14),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.TSI_BROWN),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        return total_table


def generate_daily_report_pdf(
    timesheet_data, entry_data, logo_path=None, save_backup=True
):
    """
    Generate daily report PDF with proper markup

    Args:
        timesheet_data: Dict with job_number, entry_date, job_name, company info
        entry_data: Dict with line_items, labor_entries, equipment_rental_items
        logo_path: Path to logo file
        save_backup: If True, saves PDF backup

    Returns:
        BytesIO buffer containing PDF
    """
    generator = TSIReportGenerator(logo_path=logo_path)
    return generator.generate_report(
        timesheet_data, entry_data, save_backup=save_backup
    )
