"""
Invoice Generator - TSI Branded Design
Creates professional PDF invoices with TSI logo and color scheme
Includes automatic PDF backup functionality
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
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
from io import BytesIO
import os


class TSIInvoiceGenerator:
    """Professional invoice generator with TSI branding"""

    # TSI Brand Colors
    TSI_BROWN = colors.HexColor("#8B6F47")  # TSI logo brown
    TSI_DARK_BROWN = colors.HexColor("#6B5637")  # Darker brown for text
    TSI_BLUE = colors.HexColor("#1e3a8a")  # Navy blue for accents
    GRAY_DARK = colors.HexColor("#1f2937")  # Dark gray for text
    GRAY_MED = colors.HexColor("#6b7280")  # Medium gray
    GRAY_LIGHT = colors.HexColor("#f3f4f6")  # Light gray for backgrounds

    def __init__(self, logo_path=None):
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()
        self.logo_path = logo_path or "logo.png"  # TSI logo
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup TSI-branded styles"""

        # Company name - TSI Brown
        self.styles.add(
            ParagraphStyle(
                name="CompanyName",
                parent=self.styles["Normal"],
                fontSize=18,
                textColor=self.TSI_BROWN,
                fontName="Helvetica-Bold",
                spaceAfter=2,
                leading=22,
                wordWrap="LTR",
            )
        )

        # Invoice title
        self.styles.add(
            ParagraphStyle(
                name="InvoiceTitle",
                parent=self.styles["Normal"],
                fontSize=20,
                textColor=self.TSI_BROWN,
                alignment=TA_RIGHT,
                fontName="Helvetica-Bold",
            )
        )

        # Section headers
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=self.TSI_DARK_BROWN,
                fontName="Helvetica-Bold",
                spaceAfter=3,
            )
        )

        # Small text
        self.styles.add(
            ParagraphStyle(
                name="SmallText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=self.GRAY_DARK,
            )
        )

        # Table text
        self.styles.add(
            ParagraphStyle(
                name="TableText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=self.GRAY_DARK,
            )
        )

    def generate_invoice(
        self,
        invoice_data,
        labor_total,
        materials_total,
        passthrough_total=0,
        save_backup=True,
    ):
        """
        Generate TSI-branded invoice PDF

        Args:
            invoice_data: Dictionary with invoice details
            labor_total: Total labor cost
            materials_total: Total materials + equipment cost
            passthrough_total: Total pass-through expenses
            save_backup: If True, saves PDF to invoices/ directory

        Returns:
            BytesIO buffer containing PDF
        """
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

        # Header with logo
        story.extend(self._create_header(invoice_data))
        story.append(Spacer(1, 0.2 * inch))

        # Separator line
        story.append(self._create_line())
        story.append(Spacer(1, 0.2 * inch))

        # Invoice details
        story.extend(self._create_invoice_details(invoice_data))
        story.append(Spacer(1, 0.3 * inch))

        # Line items
        story.append(
            self._create_line_items_table(
                labor_total, materials_total, passthrough_total
            )
        )
        story.append(Spacer(1, 0.4 * inch))

        # Total
        story.append(
            self._create_total_section(
                labor_total + materials_total + passthrough_total
            )
        )

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Save backup copy if requested
        if save_backup:
            self._save_backup_pdf(buffer, invoice_data)
            buffer.seek(0)  # Reset buffer after reading for backup

        return buffer

    def _save_backup_pdf(self, buffer, invoice_data):
        """Save a backup copy of the invoice to invoices/ directory"""
        try:
            # Create invoices directory if it doesn't exist
            invoices_dir = "invoices"
            os.makedirs(invoices_dir, exist_ok=True)

            # Generate filename
            date_suffix = datetime.now().strftime("%m%d%y")
            invoice_number = f"{invoice_data['job_number']}-{date_suffix}"
            filename = f"Invoice_{invoice_number}.pdf"
            filepath = os.path.join(invoices_dir, filename)

            # Save the PDF
            with open(filepath, "wb") as f:
                f.write(buffer.getvalue())

            print(f"âœ“ Invoice backup saved: {filepath}")
        except Exception as e:
            print(f"Warning: Could not save invoice backup: {e}")

    def _create_line(self):
        """Create TSI brown separator line"""
        line_data = [["", ""]]
        line_table = Table(line_data, colWidths=[7 * inch])
        line_table.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, 0), 1.5, self.TSI_BROWN),
                ]
            )
        )
        return line_table

    def _create_header(self, data):
        """Create header with TSI logo and company info"""
        elements = []

        # Try to include logo
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
                print(f"Warning: Could not load logo from {self.logo_path}")

        # Header layout: Logo + Company Name | Invoice Title
        if logo_element:
            # With logo
            header_data = [
                [
                    logo_element,
                    Paragraph(data["company_name"], self.styles["CompanyName"]),
                    Paragraph("T&amp;M INVOICE", self.styles["InvoiceTitle"]),
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
            # Without logo
            header_data = [
                [
                    Paragraph(data["company_name"], self.styles["CompanyName"]),
                    Paragraph("T&amp;M INVOICE", self.styles["InvoiceTitle"]),
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

        # Company contact info
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

    def _create_invoice_details(self, data):
        """Create invoice details section"""
        elements = []

        # Invoice metadata
        invoice_date = datetime.now().strftime("%m/%d/%Y")
        due_date = (
            datetime.now() + timedelta(days=data.get("payment_terms_days", 30))
        ).strftime("%m/%d/%Y")
        date_suffix = datetime.now().strftime("%m%d%y")
        invoice_number = f"{data['job_number']}-{date_suffix}"

        # Three columns
        bill_to_content = [
            Paragraph("<b>Bill To:</b>", self.styles["SectionHeader"]),
            Paragraph(
                f"{data['bill_to_name']}<br/>{data['bill_to_address_line1']}<br/>{data['bill_to_address_line2']}",
                self.styles["SmallText"],
            ),
        ]

        ship_to_content = [
            Paragraph("<b>Ship To:</b>", self.styles["SectionHeader"]),
            Paragraph(data["ship_to_location"], self.styles["SmallText"]),
        ]

        # Invoice metadata
        metadata_rows = [
            [
                Paragraph("<b>Invoice #:</b>", self.styles["SmallText"]),
                Paragraph(invoice_number, self.styles["SmallText"]),
            ],
            [
                Paragraph("<b>Invoice Date:</b>", self.styles["SmallText"]),
                Paragraph(invoice_date, self.styles["SmallText"]),
            ],
            [
                Paragraph("<b>Due Date:</b>", self.styles["SmallText"]),
                Paragraph(due_date, self.styles["SmallText"]),
            ],
        ]

        if data.get("purchase_order"):
            metadata_rows.append(
                [
                    Paragraph("<b>PO #:</b>", self.styles["SmallText"]),
                    Paragraph(data["purchase_order"], self.styles["SmallText"]),
                ]
            )

        if data.get("period_start") and data.get("period_end"):
            metadata_rows.append(
                [
                    Paragraph("<b>Period:</b>", self.styles["SmallText"]),
                    Paragraph(
                        f"{data['period_start']} - {data['period_end']}",
                        self.styles["SmallText"],
                    ),
                ]
            )

        metadata_table = Table(metadata_rows, colWidths=[1 * inch, 1.4 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        # Main details table
        details_data = [
            [
                bill_to_content[0],
                ship_to_content[0],
                Paragraph("<b>Invoice Details:</b>", self.styles["SectionHeader"]),
            ],
            [bill_to_content[1], ship_to_content[1], metadata_table],
        ]

        details_table = Table(
            details_data, colWidths=[2.3 * inch, 2.2 * inch, 2.5 * inch]
        )
        details_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        elements.append(details_table)

        # Remit to
        if data.get("remit_to_email"):
            elements.append(Spacer(1, 0.15 * inch))
            remit_para = Paragraph(
                f"<b>Remit To:</b> {data['remit_to_email']}", self.styles["SmallText"]
            )
            elements.append(remit_para)

        return elements

    def _create_line_items_table(
        self, labor_total, materials_total, passthrough_total=0
    ):
        """Create TSI-branded line items table"""

        # Build table data
        data = [
            [
                Paragraph("<b>Item</b>", self.styles["TableText"]),
                Paragraph("<b>Description</b>", self.styles["TableText"]),
                Paragraph("<b>Amount</b>", self.styles["TableText"]),
            ],
            [
                Paragraph("1.0", self.styles["TableText"]),
                Paragraph("TSI Labor", self.styles["TableText"]),
                Paragraph(f"${labor_total:,.2f}", self.styles["TableText"]),
            ],
            [
                Paragraph("2.0", self.styles["TableText"]),
                Paragraph("TSI Equipment and Materials", self.styles["TableText"]),
                Paragraph(f"${materials_total:,.2f}", self.styles["TableText"]),
            ],
        ]

        if passthrough_total > 0:
            data.append(
                [
                    Paragraph("3.0", self.styles["TableText"]),
                    Paragraph("Pass-Through Expenses", self.styles["TableText"]),
                    Paragraph(f"${passthrough_total:,.2f}", self.styles["TableText"]),
                ]
            )

        table = Table(data, colWidths=[0.6 * inch, 5 * inch, 1.4 * inch])

        # TSI-branded styling
        table.setStyle(
            TableStyle(
                [
                    # Header row - TSI brown background
                    ("BACKGROUND", (0, 0), (-1, 0), self.GRAY_LIGHT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.TSI_DARK_BROWN),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("TOPPADDING", (0, 0), (-1, 0), 10),
                    # Data rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TOPPADDING", (0, 1), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    # Alignment
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    # Borders - TSI brown
                    ("LINEBELOW", (0, 0), (-1, 0), 1.5, self.TSI_BROWN),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#e5e7eb")),
                    ("BOX", (0, 0), (-1, -1), 1, self.TSI_BROWN),
                ]
            )
        )

        return table

    def _create_total_section(self, grand_total):
        """Create TSI-branded total section"""

        total_data = [
            [
                Paragraph("<b>Invoice Total:</b>", self.styles["Normal"]),
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
                    ("LINEABOVE", (0, 0), (-1, 0), 2, self.TSI_BROWN),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        return total_table


def generate_invoice_pdf(
    invoice_data,
    labor_total,
    materials_total,
    passthrough_total=0,
    logo_path=None,
    save_backup=True,
):
    """
    Generate TSI-branded invoice PDF with automatic backup

    Args:
        invoice_data: Dictionary with all invoice details
        labor_total: Total labor cost (float)
        materials_total: Total materials cost (float)
        passthrough_total: Total pass-through expenses (float)
        logo_path: Path to TSI logo file (default: "logo.png")
        save_backup: If True, saves PDF to invoices/ directory (default: True)

    Returns:
        BytesIO buffer containing PDF
    """
    generator = TSIInvoiceGenerator(logo_path=logo_path)
    return generator.generate_invoice(
        invoice_data,
        labor_total,
        materials_total,
        passthrough_total,
        save_backup=save_backup,
    )
