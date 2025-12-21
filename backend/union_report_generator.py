"""
Union-Separated Daily Report Generator
Generates separate PDFs for each union (DC9, DC11, DC35) plus a materials/equipment report
Matches JF White Contracting Co. form format
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
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from datetime import datetime
from io import BytesIO
import os


class UnionReportGenerator:
    """Generate union-separated reports matching JF White format"""

    # Union-specific benefit rates
    UNION_RATES = {
        "DC9": {"health": 12.75, "pension": 13.33},
        "DC11": {"health": 10.80, "pension": 13.90},
        "DC35": {"health": 10.30, "pension": 11.95},
    }

    def __init__(self, logo_path=None):
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()
        self.logo_path = logo_path or "logo.png"
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup form-matching styles"""
        self.styles.add(
            ParagraphStyle(
                name="FormTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="FormText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
            )
        )

    def generate_union_report(
        self, union_code, timesheet_data, entry_data, save_backup=True
    ):
        """
        Generate report for a specific union

        Args:
            union_code: "DC9", "DC11", or "DC35"
            timesheet_data: Job and company info
            entry_data: Daily entry with labor, materials, equipment
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.5 * inch,
        )

        story = []

        # Header
        story.extend(self._create_header(timesheet_data, union_code))
        story.append(Spacer(1, 0.1 * inch))

        # Filter labor entries for this union
        union_labor = [
            labor
            for labor in entry_data.get("labor_entries", [])
            if labor.get("employee") and labor["employee"].get("union") == union_code
        ]

        if not union_labor:
            # No labor for this union
            no_data = Paragraph(
                f"<b>No {union_code} labor entries for this date</b>",
                self.styles["FormText"],
            )
            story.append(no_data)
        else:
            # Labor table for this union
            story.append(self._create_union_labor_table(union_code, union_labor))
            story.append(Spacer(1, 0.2 * inch))

            # Totals section
            story.append(self._create_union_totals(union_code, union_labor))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        if save_backup:
            self._save_backup_pdf(buffer, timesheet_data, f"LABOR_{union_code}")
            buffer.seek(0)

        return buffer

    def generate_materials_equipment_report(
        self, timesheet_data, entry_data, save_backup=True
    ):
        """
        Generate materials and equipment only report
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.5 * inch,
        )

        story = []

        # Header
        story.extend(self._create_header(timesheet_data, "MATERIALS & EQUIPMENT"))
        story.append(Spacer(1, 0.1 * inch))

        # Materials section
        if entry_data.get("line_items"):
            story.append(self._create_materials_table(entry_data["line_items"]))
            story.append(Spacer(1, 0.15 * inch))

        # Equipment section
        if entry_data.get("equipment_rental_items"):
            story.append(
                self._create_equipment_table(entry_data["equipment_rental_items"])
            )
            story.append(Spacer(1, 0.15 * inch))

        # Totals
        story.append(self._create_materials_equipment_totals(entry_data))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        if save_backup:
            self._save_backup_pdf(buffer, timesheet_data, "MATERIALS_EQUIPMENT")
            buffer.seek(0)

        return buffer

    def _create_header(self, data, section_title):
        """Create form header with company and job information"""
        elements = []

        # Get company info from data or use defaults (handle empty strings)
        company_name = data.get("company_name") or "Tri-State Painting, LLC"
        job_name = data.get("job_name") or "Dutch Point T&M"

        # Company info table
        header_data = [
            [
                Paragraph(f"<b>{company_name}</b>", self.styles["FormTitle"]),
                Paragraph(
                    f"<b>DATE:</b><br/>{data.get('entry_date', '')}",
                    self.styles["FormText"],
                ),
            ],
            [
                Paragraph(
                    "612 West Main Street Unit 2<br/>Tilton, NH 03276<br/>(603) 286-7657",
                    self.styles["FormText"],
                ),
                Paragraph(
                    f"<b>Job No.</b><br/>{data.get('job_number', '')}",
                    self.styles["FormText"],
                ),
            ],
            [
                Paragraph(f"<b>{job_name}</b>", self.styles["FormTitle"]),
                Paragraph(
                    f"<b>Entry Date:</b><br/>{data.get('entry_date', '')}",
                    self.styles["FormText"],
                ),
            ],
        ]

        header_table = Table(header_data, colWidths=[4 * inch, 3 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(header_table)

        # Section title
        elements.append(Spacer(1, 0.1 * inch))
        title = Paragraph(f"<b>{section_title}</b>", self.styles["SectionHeader"])
        elements.append(title)
        elements.append(Spacer(1, 0.05 * inch))

        return elements

    def _create_union_labor_table(self, union_code, labor_entries):
        """Create labor table for specific union"""

        # Get union-specific rates
        rates = self.UNION_RATES.get(union_code, {"health": 12.75, "pension": 13.33})
        hw_rate = rates["health"]
        pension_rate = rates["pension"]

        # Header
        table_data = [
            [
                Paragraph("<b>Class</b>", self.styles["FormText"]),
                Paragraph("<b>No.</b>", self.styles["FormText"]),
                Paragraph("<b>Total<br/>Hours</b>", self.styles["FormText"]),
                Paragraph("<b>Rate</b>", self.styles["FormText"]),
                Paragraph("<b>Amount</b>", self.styles["FormText"]),
            ]
        ]

        total_labor = 0

        for labor in labor_entries:
            employee = labor.get("employee", {})
            employee_name = employee.get(
                "full_name", labor.get("employee_name", "Unknown")
            )

            # Separate ST and OT entries
            reg_hours = float(labor.get("regular_hours", 0))
            ot_hours = float(labor.get("overtime_hours", 0))

            reg_rate = float(
                employee.get("regular_rate", labor.get("straight_rate", 0))
            )
            ot_rate = float(
                employee.get("overtime_rate", labor.get("overtime_rate", 0))
            )

            # Add night shift differential if applicable
            if labor.get("night_shift"):
                reg_rate += 2.00
                ot_rate += 2.00

            # Regular hours row
            if reg_hours > 0:
                reg_amount = reg_hours * reg_rate
                total_labor += reg_amount

                table_data.append(
                    [
                        Paragraph(f"{employee_name} (ST)", self.styles["FormText"]),
                        "",
                        Paragraph(f"{reg_hours:.1f}", self.styles["FormText"]),
                        Paragraph(f"$ {reg_rate:.2f}", self.styles["FormText"]),
                        Paragraph(f"$ {reg_amount:.2f}", self.styles["FormText"]),
                    ]
                )

            # Overtime hours row
            if ot_hours > 0:
                ot_amount = ot_hours * ot_rate
                total_labor += ot_amount

                table_data.append(
                    [
                        Paragraph(f"{employee_name} (OT)", self.styles["FormText"]),
                        "",
                        Paragraph(f"{ot_hours:.1f}", self.styles["FormText"]),
                        Paragraph(f"$ {ot_rate:.2f}", self.styles["FormText"]),
                        Paragraph(f"$ {ot_amount:.2f}", self.styles["FormText"]),
                    ]
                )

        # Total row
        table_data.append(
            [
                Paragraph("<b>Total Labor</b>", self.styles["FormText"]),
                "",
                "",
                "",
                Paragraph(f"<b>$ {total_labor:,.2f}</b>", self.styles["FormText"]),
            ]
        )

        # Calculate benefits using union-specific rates
        total_hours = sum(
            float(l.get("regular_hours", 0)) + float(l.get("overtime_hours", 0))
            for l in labor_entries
        )

        # Health & Welfare row
        hw_amount = total_hours * hw_rate
        table_data.append(
            [
                Paragraph("Health", self.styles["FormText"]),
                Paragraph("op", self.styles["FormText"]),
                Paragraph(f"{total_hours:.1f}", self.styles["FormText"]),
                Paragraph(f"$ {hw_rate:.2f}", self.styles["FormText"]),
                Paragraph(f"$ {hw_amount:.2f}", self.styles["FormText"]),
            ]
        )

        # Welfare row
        table_data.append(
            [
                Paragraph("Welfare", self.styles["FormText"]),
                Paragraph("lab", self.styles["FormText"]),
                "",
                "",
                Paragraph("$ -", self.styles["FormText"]),
            ]
        )

        # Pension row
        pension_amount = total_hours * pension_rate
        table_data.append(
            [
                Paragraph("Pension", self.styles["FormText"]),
                Paragraph("team", self.styles["FormText"]),
                Paragraph(f"{total_hours:.1f}", self.styles["FormText"]),
                Paragraph(f"$ {pension_rate:.2f}", self.styles["FormText"]),
                Paragraph(f"$ {pension_amount:.2f}", self.styles["FormText"]),
            ]
        )

        table = Table(
            table_data,
            colWidths=[2.8 * inch, 0.5 * inch, 1.0 * inch, 1.2 * inch, 1.5 * inch],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, -4), (0, -1), "Helvetica-Bold"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        return table

    def _create_materials_table(self, line_items):
        """Create materials table"""

        # Header
        table_data = [
            [
                Paragraph("<b>Description</b>", self.styles["FormText"]),
                Paragraph("<b>Quantity</b>", self.styles["FormText"]),
                Paragraph("<b>Unit<br/>Price</b>", self.styles["FormText"]),
                Paragraph("<b>Amount</b>", self.styles["FormText"]),
            ]
        ]

        materials_total = 0

        for item in line_items:
            qty = float(item.get("quantity", 0))
            price = float(item.get("unit_price", 0))
            amount = qty * price
            materials_total += amount

            table_data.append(
                [
                    Paragraph(item.get("material_name", ""), self.styles["FormText"]),
                    Paragraph(
                        f"{qty:.0f}" if qty == int(qty) else f"{qty:.2f}",
                        self.styles["FormText"],
                    ),
                    Paragraph(f"$ {price:.2f}", self.styles["FormText"]),
                    Paragraph(f"$ {amount:.2f}", self.styles["FormText"]),
                ]
            )

        # Material Total
        table_data.append(
            [
                Paragraph("<b>Material Total</b>", self.styles["FormText"]),
                "",
                "",
                Paragraph(f"<b>$ {materials_total:.2f}</b>", self.styles["FormText"]),
            ]
        )

        # 15% Markup
        markup = materials_total * 0.15
        table_data.append(
            [
                Paragraph("<b>15% Material Markup</b>", self.styles["FormText"]),
                "",
                "",
                Paragraph(f"<b>$ {markup:.2f}</b>", self.styles["FormText"]),
            ]
        )

        table = Table(
            table_data,
            colWidths=[3.5 * inch, 1 * inch, 1.2 * inch, 1.3 * inch],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("FONTNAME", (0, -2), (0, -1), "Helvetica-Bold"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        return table

    def _create_equipment_table(self, equipment_items):
        """Create equipment table"""

        # Header
        table_data = [
            [
                Paragraph("<b>Size & Class</b>", self.styles["FormText"]),
                Paragraph("<b>No.<br/>Pieces</b>", self.styles["FormText"]),
                Paragraph("<b>Total<br/>Hours</b>", self.styles["FormText"]),
                Paragraph("<b>Rate</b>", self.styles["FormText"]),
                Paragraph("<b>Amount</b>", self.styles["FormText"]),
            ]
        ]

        equipment_total = 0

        for item in equipment_items:
            qty = float(item.get("quantity", 0))
            rate = float(item.get("unit_rate", 0))
            amount = qty * rate
            equipment_total += amount

            # Assume 1 piece
            pieces = 1
            hours = qty

            table_data.append(
                [
                    Paragraph(item.get("equipment_name", ""), self.styles["FormText"]),
                    Paragraph(f"{pieces}", self.styles["FormText"]),
                    Paragraph(f"{hours:.1f}", self.styles["FormText"]),
                    Paragraph(f"$ {rate:.2f}", self.styles["FormText"]),
                    Paragraph(f"$ {amount:.2f}", self.styles["FormText"]),
                ]
            )

        # Equipment Total
        table_data.append(
            [
                Paragraph("<b>Equipment Total</b>", self.styles["FormText"]),
                "",
                "",
                "",
                Paragraph(f"<b>$ {equipment_total:.2f}</b>", self.styles["FormText"]),
            ]
        )

        table = Table(
            table_data,
            colWidths=[2.5 * inch, 0.8 * inch, 1 * inch, 1.2 * inch, 1.5 * inch],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("FONTNAME", (0, -1), (0, -1), "Helvetica-Bold"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        return table

    def _create_empty_materials_section(self):
        """Create empty materials section (per union reports in images)"""
        table_data = [
            [
                Paragraph("<b>MATERIALS</b>", self.styles["SectionHeader"]),
                "",
                "",
                "",
            ],
            ["", "", "", ""],
        ]

        table = Table(
            table_data, colWidths=[3.5 * inch, 1 * inch, 1.2 * inch, 1.3 * inch]
        )
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("SPAN", (0, 0), (-1, 0)),
                ]
            )
        )
        return table

    def _create_empty_equipment_section(self):
        """Create empty equipment section"""
        table_data = [
            [
                Paragraph("<b>EQUIPMENT</b>", self.styles["SectionHeader"]),
                "",
            ],
            ["Equipment Total", "$ -"],
        ]

        table = Table(table_data, colWidths=[5.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("ALIGN", (1, 1), (1, 1), "RIGHT"),
                ]
            )
        )
        return table

    def _create_union_totals(self, union_code, labor_entries):
        """Create totals section for union report - FIXED to use employee rates and add 20% markup"""

        # Get union-specific rates
        rates = self.UNION_RATES.get(union_code, {"health": 12.75, "pension": 13.33})
        hw_rate = rates["health"]
        pension_rate = rates["pension"]

        # ✅ FIX #1: Calculate labor total using EMPLOYEE RATES (not labor_role rates)
        labor_total = 0
        for labor in labor_entries:
            employee = labor.get("employee", {})
            reg_hours = float(labor.get("regular_hours", 0))
            ot_hours = float(labor.get("overtime_hours", 0))

            # Use employee rates if available, otherwise fall back to labor entry rates
            reg_rate = float(
                employee.get("regular_rate", labor.get("straight_rate", 0))
            )
            ot_rate = float(
                employee.get("overtime_rate", labor.get("overtime_rate", 0))
            )

            # Add night shift differential if applicable
            if labor.get("night_shift"):
                reg_rate += 2.00
                ot_rate += 2.00

            labor_total += (reg_hours * reg_rate) + (ot_hours * ot_rate)

        # Calculate total hours
        total_hours = sum(
            float(l.get("regular_hours", 0)) + float(l.get("overtime_hours", 0))
            for l in labor_entries
        )

        # Benefits using union-specific rates
        health_welfare = total_hours * hw_rate
        pension = total_hours * pension_rate

        # ✅ FIX #2: Calculate subtotal (Items 1+2+3, where Item 3 is always $0 for now)
        subtotal = labor_total + health_welfare + pension

        # ✅ FIX #3: Apply 20% markup
        markup_20 = subtotal * 0.20

        # ✅ FIX #4: Contractor total (Items 1 through 5)
        contractor_total = subtotal + markup_20

        totals_data = [
            [
                Paragraph("<b>Contractor TOTAL</b>", self.styles["FormText"]),
                Paragraph(f"<b>$ {contractor_total:,.2f}</b>", self.styles["FormText"]),
            ]
        ]

        totals_table = Table(totals_data, colWidths=[5.5 * inch, 1.5 * inch])
        totals_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 2, colors.black),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        return totals_table

    def _create_materials_equipment_totals(self, entry_data):
        """Create totals for materials/equipment report"""

        materials_total = sum(
            item.get("total_amount", 0) for item in entry_data.get("line_items", [])
        )

        equipment_total = sum(
            item.get("total_amount", 0)
            for item in entry_data.get("equipment_rental_items", [])
        )

        materials_markup = materials_total * 0.15

        contractor_total = materials_total + materials_markup + equipment_total

        totals_data = [
            [
                Paragraph("<b>Contractor TOTAL</b>", self.styles["FormText"]),
                Paragraph(f"<b>$ {contractor_total:,.2f}</b>", self.styles["FormText"]),
            ]
        ]

        totals_table = Table(totals_data, colWidths=[5.5 * inch, 1.5 * inch])
        totals_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 2, colors.black),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        return totals_table

    def _save_backup_pdf(self, buffer, timesheet_data, report_type):
        """Save backup copy"""
        try:
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)

            job_number = timesheet_data["job_number"]
            date = timesheet_data["entry_date"]
            filename = f"JFW_{report_type}_{job_number}_{date}.pdf"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, "wb") as f:
                f.write(buffer.getvalue())

            print(f"✅ Report saved: {filepath}")
        except Exception as e:
            print(f"Warning: Could not save report backup: {e}")


def generate_all_union_reports(timesheet_data, entry_data, logo_path=None):
    """
    Generate all reports: DC9, DC11, DC35, and Materials/Equipment

    Returns dict with PDFs:
    {
        'DC9': BytesIO buffer,
        'DC11': BytesIO buffer,
        'DC35': BytesIO buffer,
        'MATERIALS_EQUIPMENT': BytesIO buffer
    }
    """
    generator = UnionReportGenerator(logo_path=logo_path)
    reports = {}

    # Generate union reports
    for union in ["DC9", "DC11", "DC35"]:
        reports[union] = generator.generate_union_report(
            union, timesheet_data, entry_data, save_backup=True
        )

    # Generate materials/equipment report
    reports["MATERIALS_EQUIPMENT"] = generator.generate_materials_equipment_report(
        timesheet_data, entry_data, save_backup=True
    )

    return reports
