"""
Invoice Generator - Creates PDF invoices using ReportLab
Matches TSI invoice format with 2 line items: Labor + Materials
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
from io import BytesIO


class InvoiceGenerator:
    def __init__(self):
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(
            ParagraphStyle(
                name="CompanyName",
                parent=self.styles["Normal"],
                fontSize=16,
                textColor=colors.HexColor("#1a56db"),
                spaceAfter=6,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="InvoiceTitle",
                parent=self.styles["Normal"],
                fontSize=14,
                textColor=colors.HexColor("#1a56db"),
                alignment=TA_RIGHT,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#374151"),
                fontName="Helvetica-Bold",
                spaceAfter=4,
            )
        )

    def generate_invoice(self, invoice_data, labor_total, materials_total):
        """
        Generate invoice PDF

        Args:
            invoice_data: Dictionary with invoice details
            labor_total: Total labor cost
            materials_total: Total materials cost

        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build invoice content
        story = []

        # Header section
        story.extend(self._create_header(invoice_data))
        story.append(Spacer(1, 0.3 * inch))

        # Invoice details section
        story.extend(self._create_invoice_details(invoice_data))
        story.append(Spacer(1, 0.3 * inch))

        # Line items table
        story.append(self._create_line_items_table(labor_total, materials_total))
        story.append(Spacer(1, 0.3 * inch))

        # Total section
        story.append(self._create_total_section(labor_total + materials_total))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_header(self, data):
        """Create invoice header with company info and title"""
        elements = []

        # Create header table (company info on left, invoice title on right)
        header_data = [
            [
                Paragraph(data["company_name"], self.styles["CompanyName"]),
                Paragraph("T&M INVOICE", self.styles["InvoiceTitle"]),
            ],
            [
                Paragraph(
                    f"{data['company_address_line1']}<br/>{data['company_address_line2']}",
                    self.styles["Normal"],
                ),
                "",
            ],
            [Paragraph(f"Phone: {data['company_phone']}", self.styles["Normal"]), ""],
        ]

        if data.get("company_fax"):
            header_data.append(
                [Paragraph(f"Fax: {data['company_fax']}", self.styles["Normal"]), ""]
            )

        header_table = Table(header_data, colWidths=[4 * inch, 2.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]
            )
        )

        elements.append(header_table)
        return elements

    def _create_invoice_details(self, data):
        """Create invoice metadata and bill-to section"""
        elements = []

        # Invoice metadata (right side)
        invoice_date = datetime.now().strftime("%m/%d/%Y")
        due_date = (
            datetime.now() + timedelta(days=data.get("payment_terms_days", 30))
        ).strftime("%m/%d/%Y")

        # Generate invoice number: {job_number}-{MMDDYY}
        date_suffix = datetime.now().strftime("%m%d%y")
        invoice_number = f"{data['job_number']}-{date_suffix}"

        metadata_data = [
            ["Invoice #:", invoice_number],
            ["Invoice Date:", invoice_date],
            ["Due Date:", due_date],
        ]

        if data.get("purchase_order"):
            metadata_data.append(["PO #:", data["purchase_order"]])

        if data.get("period_start") and data.get("period_end"):
            metadata_data.append(
                ["Period:", f"{data['period_start']} - {data['period_end']}"]
            )

        metadata_table = Table(metadata_data, colWidths=[1.2 * inch, 1.8 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#374151")),
                ]
            )
        )

        # Bill To and Ship To section
        bill_to_header = Paragraph("<b>Bill To:</b>", self.styles["SectionHeader"])
        bill_to_text = Paragraph(
            f"{data['bill_to_name']}<br/>{data['bill_to_address_line1']}<br/>{data['bill_to_address_line2']}",
            self.styles["Normal"],
        )

        ship_to_header = Paragraph("<b>Ship To:</b>", self.styles["SectionHeader"])
        ship_to_text = Paragraph(data["ship_to_location"], self.styles["Normal"])

        # Combine in table layout
        details_data = [
            [bill_to_header, ship_to_header, metadata_table],
            [bill_to_text, ship_to_text, ""],
        ]

        details_table = Table(
            details_data, colWidths=[2.5 * inch, 1.5 * inch, 2.5 * inch]
        )
        details_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("SPAN", (2, 0), (2, 1)),  # Metadata spans both rows
                ]
            )
        )

        elements.append(details_table)

        # Remit to email if provided
        if data.get("remit_to_email"):
            elements.append(Spacer(1, 0.1 * inch))
            remit_para = Paragraph(
                f"<b>Remit To:</b> {data['remit_to_email']}", self.styles["Normal"]
            )
            elements.append(remit_para)

        return elements

    def _create_line_items_table(self, labor_total, materials_total):
        """Create line items table with labor and materials"""
        # Table data
        data = [
            ["Item", "Description", "Amount"],  # Header
            ["1.0", "TSI Labor", f"${labor_total:,.2f}"],
            ["2.0", "Equipment and Materials", f"${materials_total:,.2f}"],
        ]

        # Create table
        table = Table(data, colWidths=[0.8 * inch, 4 * inch, 1.7 * inch])

        # Style the table
        table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#374151")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    # Data rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    # Alignment
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),  # Item column
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),  # Description
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),  # Amount
                    # Grid
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#d1d5db")),
                ]
            )
        )

        return table

    def _create_total_section(self, grand_total):
        """Create total section at bottom"""
        total_data = [["Invoice Total:", f"${grand_total:,.2f}"]]

        total_table = Table(total_data, colWidths=[5.5 * inch, 1.0 * inch])
        total_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a56db")),
                    ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.HexColor("#1a56db")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        return total_table


def generate_invoice_pdf(invoice_data, labor_total, materials_total):
    """
    Convenience function to generate invoice PDF

    Args:
        invoice_data: Dictionary with all invoice details
        labor_total: Total labor cost (float)
        materials_total: Total materials cost (float)

    Returns:
        BytesIO buffer containing PDF
    """
    generator = InvoiceGenerator()
    return generator.generate_invoice(invoice_data, labor_total, materials_total)
