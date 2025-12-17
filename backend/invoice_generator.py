"""
Invoice Generator - T&M Invoice PDF
Aggregates multiple daily entries into a formal invoice
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
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from datetime import datetime, timedelta
from io import BytesIO
import os


class TSIInvoiceGenerator:
    """TSI Invoice generator matching company format"""

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
        """Setup invoice-specific styles"""
        self.styles.add(
            ParagraphStyle(
                name="InvoiceTitle",
                parent=self.styles["Normal"],
                fontSize=24,
                textColor=self.TSI_DARK_BROWN,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                spaceAfter=20,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionLabel",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="TableHeader",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CellText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SmallText",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=self.GRAY_DARK,
            )
        )

    def generate_invoice(self, invoice_data, line_items, save_backup=True):
        """
        Generate invoice PDF

        Args:
            invoice_data: Dict with invoice metadata (invoice_number, dates, client info, etc.)
            line_items: List of aggregated line items for the invoice
            save_backup: If True, saves PDF backup

        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        story = []

        # Header with logo and title
        story.extend(self._create_header())
        story.append(Spacer(1, 0.1 * inch))

        # Company info and invoice metadata
        story.extend(self._create_invoice_metadata(invoice_data))
        story.append(Spacer(1, 0.15 * inch))

        # Bill To / Ship To section
        story.extend(self._create_billing_section(invoice_data))
        story.append(Spacer(1, 0.15 * inch))

        # Line items table
        story.append(self._create_line_items_table(line_items))
        story.append(Spacer(1, 0.1 * inch))

        # Totals
        story.append(self._create_totals_section(line_items))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        if save_backup:
            self._save_backup_pdf(buffer, invoice_data)
            buffer.seek(0)

        return buffer

    def _create_header(self):
        """Create header with logo and title"""
        elements = []

        # Logo and Title side by side
        logo_element = None
        if os.path.exists(self.logo_path):
            try:
                logo = Image(
                    self.logo_path,
                    width=1.8 * inch,
                    height=0.95 * inch,
                    kind="proportional",
                )
                logo_element = logo
            except:
                pass

        if logo_element:
            header_data = [
                [
                    logo_element,
                    Paragraph("T&M INVOICE", self.styles["InvoiceTitle"]),
                ]
            ]
            header_table = Table(header_data, colWidths=[2 * inch, 5.5 * inch])
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ]
                )
            )
            elements.append(header_table)
        else:
            elements.append(Paragraph("T&M INVOICE", self.styles["InvoiceTitle"]))

        return elements

    def _create_invoice_metadata(self, invoice_data):
        """Create Remit To section and invoice metadata"""
        elements = []

        # Create two-column layout: Remit To | Invoice Info
        remit_to_data = [
            [Paragraph("<b>Remit To:</b>", self.styles["SectionLabel"])],
            [
                Paragraph(
                    "<b>Tri-State Painting, LLC (TSI)</b>", self.styles["SmallText"]
                )
            ],
            [Paragraph("P.O. Box 1240", self.styles["SmallText"])],
            [Paragraph("612 West Main Street", self.styles["SmallText"])],
            [Paragraph("Tilton, NH 03276-1240", self.styles["SmallText"])],
            [
                Paragraph(
                    f"Phone {invoice_data.get('company_phone', '(603) 286-7657')}",
                    self.styles["SmallText"],
                )
            ],
            [
                Paragraph(
                    f"Fax {invoice_data.get('company_fax', '(603) 286-3807')}",
                    self.styles["SmallText"],
                )
            ],
        ]

        remit_table = Table(remit_to_data, colWidths=[3.5 * inch])
        remit_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        # Invoice metadata
        invoice_date = invoice_data.get(
            "invoice_date", datetime.now().strftime("%m/%d/%y")
        )
        due_date = invoice_data.get("due_date", "")

        metadata_data = [
            [
                Paragraph("<b>Invoice Date:</b>", self.styles["SmallText"]),
                Paragraph(invoice_date, self.styles["SmallText"]),
            ],
            [
                Paragraph("<b>Invoice #:</b>", self.styles["SmallText"]),
                Paragraph(
                    str(invoice_data.get("invoice_number", "0")),
                    self.styles["SmallText"],
                ),
            ],
            [
                Paragraph("<b>Due Date:</b>", self.styles["SmallText"]),
                Paragraph(due_date, self.styles["SmallText"]),
            ],
            [
                Paragraph("<b>Job Number:</b>", self.styles["SmallText"]),
                Paragraph(
                    invoice_data.get("purchase_order", ""), self.styles["SmallText"]
                ),
            ],
            [
                Paragraph("<b>Period:</b>", self.styles["SmallText"]),
                Paragraph(invoice_data.get("period", ""), self.styles["SmallText"]),
            ],
            [
                Paragraph("<b>Terms:</b>", self.styles["SmallText"]),
                Paragraph(
                    invoice_data.get("terms", "Net 30"), self.styles["SmallText"]
                ),
            ],
        ]

        metadata_table = Table(metadata_data, colWidths=[1.3 * inch, 2.5 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), self.GRAY_LIGHT),
                ]
            )
        )

        # Combine both sections
        combined_data = [[remit_table, metadata_table]]
        combined_table = Table(combined_data, colWidths=[3.5 * inch, 4 * inch])
        combined_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(combined_table)
        return elements

    def _create_billing_section(self, invoice_data):
        """Create Bill To and Ship To section"""
        elements = []

        # Bill To
        bill_to_data = [
            [Paragraph("<b>Bill To:</b>", self.styles["SectionLabel"])],
            [Paragraph(invoice_data.get("bill_to_name", ""), self.styles["SmallText"])],
            [
                Paragraph(
                    invoice_data.get("bill_to_address_line1", ""),
                    self.styles["SmallText"],
                )
            ],
            [
                Paragraph(
                    invoice_data.get("bill_to_address_line2", ""),
                    self.styles["SmallText"],
                )
            ],
        ]

        bill_to_table = Table(bill_to_data, colWidths=[3.5 * inch])
        bill_to_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        # Ship To
        ship_to_lines = [Paragraph("<b>Ship To:</b>", self.styles["SectionLabel"])]

        # Add location on separate line
        if invoice_data.get("ship_to_location"):
            ship_to_lines.append(
                Paragraph(
                    invoice_data.get("ship_to_location", ""), self.styles["SmallText"]
                )
            )

        if invoice_data.get("job_name"):
            ship_to_lines.append(
                Paragraph(invoice_data.get("job_name", ""), self.styles["SmallText"])
            )

        if invoice_data.get("contract_number"):
            ship_to_lines.append(
                Paragraph(
                    invoice_data.get("contract_number", ""), self.styles["SmallText"]
                )
            )

        ship_to_data = [[line] for line in ship_to_lines]

        ship_to_table = Table(ship_to_data, colWidths=[4 * inch])
        ship_to_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        # Combine both sections with border
        combined_data = [[bill_to_table, ship_to_table]]
        combined_table = Table(combined_data, colWidths=[3.5 * inch, 4 * inch])
        combined_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, 0), self.GRAY_LIGHT),
                    ("BACKGROUND", (1, 0), (1, 0), self.GRAY_LIGHT),
                ]
            )
        )

        elements.append(combined_table)
        return elements

    def _create_line_items_table(self, line_items):
        """Create the main line items table"""

        # Header row
        table_data = [
            [
                Paragraph("<b>Unit No.</b>", self.styles["TableHeader"]),
                Paragraph("<b>Description</b>", self.styles["TableHeader"]),
                Paragraph("<b>Quantity</b>", self.styles["TableHeader"]),
                Paragraph("<b>Unit Price</b>", self.styles["TableHeader"]),
                Paragraph("<b>Unit</b>", self.styles["TableHeader"]),
                Paragraph("<b>Amount</b>", self.styles["TableHeader"]),
            ]
        ]

        # Add line items
        for idx, item in enumerate(line_items, start=1):
            unit_no = f"{float(idx):.1f}"
            description = item.get("description", "")
            quantity = item.get("quantity", 1)
            unit_price = item.get("unit_price", 0.0)
            unit = item.get("unit", "Ea")
            amount = item.get("amount", 0.0)

            # Format quantity
            qty_str = (
                f"{int(quantity)}" if quantity == int(quantity) else f"{quantity:.2f}"
            )

            table_data.append(
                [
                    Paragraph(unit_no, self.styles["CellText"]),
                    Paragraph(description, self.styles["CellText"]),
                    Paragraph(qty_str, self.styles["CellText"]),
                    Paragraph(f"$ {unit_price:,.2f}", self.styles["CellText"]),
                    Paragraph(unit, self.styles["CellText"]),
                    Paragraph(f"$ {amount:,.2f}", self.styles["CellText"]),
                ]
            )

        # Column widths - match Bill To/Ship To width (7.5" total)
        col_widths = [
            0.5 * inch,  # Unit No
            3.2 * inch,  # Description
            0.9 * inch,  # Quantity
            1.0 * inch,  # Unit Price
            0.9 * inch,  # Unit
            1.0 * inch,  # Amount
        ]

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), self.GRAY_LIGHT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, 0), 1, colors.black),
                    # Data rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    # Alignment
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),  # Unit No
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),  # Description
                    ("ALIGN", (2, 0), (2, -1), "CENTER"),  # Quantity
                    ("ALIGN", (3, 0), (3, -1), "RIGHT"),  # Unit Price
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),  # Unit
                    ("ALIGN", (5, 0), (5, -1), "RIGHT"),  # Amount
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        return table

    def _create_totals_section(self, line_items):
        """Create subtotal and total section"""

        # Calculate totals
        subtotal = sum(item.get("amount", 0.0) for item in line_items)

        totals_data = [
            [
                Paragraph("<b>Subtotal</b>", self.styles["SectionLabel"]),
                f"$ {subtotal:,.2f}",
            ],
            [
                Paragraph("<b>Invoice Total</b>", self.styles["SectionLabel"]),
                f"$ {subtotal:,.2f}",
            ],
        ]

        totals_table = Table(totals_data, colWidths=[6.5 * inch, 1.0 * inch])
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), self.GRAY_LIGHT),
                    ("BACKGROUND", (0, 1), (-1, 1), self.GRAY_LIGHT),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (1, 0), (1, -1), 10),
                ]
            )
        )

        return totals_table

    def _save_backup_pdf(self, buffer, invoice_data):
        """Save a backup copy of the invoice"""
        try:
            reports_dir = "invoices"
            os.makedirs(reports_dir, exist_ok=True)

            invoice_number = invoice_data.get("invoice_number", "0")
            job_number = invoice_data.get("job_number", "unknown")
            filename = f"Invoice_{invoice_number}_{job_number}.pdf"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, "wb") as f:
                f.write(buffer.getvalue())

            print(f"âœ“ Invoice saved: {filepath}")
        except Exception as e:
            print(f"Warning: Could not save invoice backup: {e}")


def generate_invoice_pdf(invoice_data, line_items, logo_path=None, save_backup=True):
    """
    Generate invoice PDF

    Args:
        invoice_data: Dict with invoice metadata
        line_items: List of aggregated line items
        logo_path: Path to logo file
        save_backup: If True, saves PDF backup

    Returns:
        BytesIO buffer containing PDF
    """
    generator = TSIInvoiceGenerator(logo_path=logo_path)
    return generator.generate_invoice(invoice_data, line_items, save_backup=save_backup)
