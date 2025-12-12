"""
ADD THESE NEW MODELS TO YOUR database.py
Place them after the existing models
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    ForeignKey,
    Boolean,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from database import Base

# Add these two new model classes to your database.py


class EquipmentRentalRate(Base):
    """Equipment rental rates catalog"""

    __tablename__ = "equipment_rental_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=False, default="Day")
    daily_rate = Column(Numeric(10, 2))
    weekly_rate = Column(Numeric(10, 2))
    monthly_rate = Column(Numeric(10, 2))
    year = Column(String(4), nullable=False)
    effective_date = Column(Date)
    notes = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    # Relationship to line items
    rental_line_items = relationship(
        "EquipmentRentalLineItem", back_populates="equipment_rental"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "unit": self.unit,
            "daily_rate": float(self.daily_rate) if self.daily_rate else None,
            "weekly_rate": float(self.weekly_rate) if self.weekly_rate else None,
            "monthly_rate": float(self.monthly_rate) if self.monthly_rate else None,
            "year": self.year,
            "active": self.active,
        }


class EquipmentRentalLineItem(Base):
    """Equipment rental line items for daily entries"""

    __tablename__ = "equipment_rental_line_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_entry_id = Column(
        Integer, ForeignKey("daily_entries.id", ondelete="CASCADE"), nullable=False
    )
    equipment_rental_id = Column(
        Integer, ForeignKey("equipment_rental_rates.id"), nullable=False
    )
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    rate_period = Column(String(20), nullable=False, default="daily")
    unit_rate = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2))

    # Relationships
    daily_entry = relationship("DailyEntry", back_populates="equipment_rental_items")
    equipment_rental = relationship(
        "EquipmentRentalRate", back_populates="rental_line_items"
    )

    @property
    def calculated_total(self):
        return float(self.quantity) * float(self.unit_rate)

    def to_dict(self):
        return {
            "id": self.id,
            "equipment_rental_id": self.equipment_rental_id,
            "equipment_name": self.equipment_rental.name,
            "category": self.equipment_rental.category,
            "quantity": float(self.quantity),
            "rate_period": self.rate_period,
            "unit_rate": float(self.unit_rate),
            "total_amount": self.calculated_total,
        }

    # ALSO UPDATE THE DailyEntry MODEL
    # Add this relationship to your existing DailyEntry class:

    # Add this line to DailyEntry relationships:
    equipment_rental_items = relationship(
        "EquipmentRentalLineItem",
        back_populates="daily_entry",
        cascade="all, delete-orphan",
    )

    # Update the to_dict method to include equipment rentals:
    def to_dict(self):
        return {
            "id": self.id,
            "job_number": self.job_number,
            "entry_date": str(self.entry_date),
            "line_items": [item.to_dict() for item in self.line_items],
            "labor_entries": [labor.to_dict() for labor in self.labor_entries],
            "equipment_rental_items": [
                equip.to_dict() for equip in self.equipment_rental_items
            ],
        }
