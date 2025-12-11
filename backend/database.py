"""
Database Models - SQLAlchemy with SQLite
Updated with Labor Tracking Support + Multiple Employees Per Role
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import date
from decimal import Decimal

Base = declarative_base()


class Material(Base):
    """Master materials catalog with pricing"""

    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Relationship to line items
    line_items = relationship("EntryLineItem", back_populates="material")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "unit_price": float(self.unit_price),
        }


class LaborRole(Base):
    """Master labor roles catalog with rates"""

    __tablename__ = "labor_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(50), nullable=False, default="LABOR")
    straight_rate = Column(Numeric(10, 2), nullable=False)
    overtime_rate = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(50), nullable=False, default="Hour")

    # Relationship to labor entries
    labor_entries = relationship("LaborEntry", back_populates="labor_role")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "straight_rate": float(self.straight_rate),
            "overtime_rate": float(self.overtime_rate),
            "unit": self.unit,
        }


class DailyEntry(Base):
    """Daily timesheet entry (one per day per job)"""

    __tablename__ = "daily_entries"
    __table_args__ = (
        UniqueConstraint("job_number", "entry_date", name="unique_job_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_number = Column(String(50), nullable=False)
    entry_date = Column(Date, nullable=False)

    # Relationships
    line_items = relationship(
        "EntryLineItem", back_populates="daily_entry", cascade="all, delete-orphan"
    )
    labor_entries = relationship(
        "LaborEntry", back_populates="daily_entry", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "job_number": self.job_number,
            "entry_date": str(self.entry_date),
            "line_items": [item.to_dict() for item in self.line_items],
            "labor_entries": [labor.to_dict() for labor in self.labor_entries],
        }


class EntryLineItem(Base):
    """Individual material line item for a daily entry"""

    __tablename__ = "entry_line_items"
    __table_args__ = (
        UniqueConstraint("daily_entry_id", "material_id", name="unique_entry_material"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_entry_id = Column(
        Integer, ForeignKey("daily_entries.id", ondelete="CASCADE"), nullable=False
    )
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    daily_entry = relationship("DailyEntry", back_populates="line_items")
    material = relationship("Material", back_populates="line_items")

    @property
    def total_amount(self):
        return float(self.quantity) * float(self.unit_price)

    def to_dict(self):
        return {
            "id": self.id,
            "material_id": self.material_id,
            "material_name": self.material.name,
            "category": self.material.category,
            "unit": self.material.unit,
            "quantity": float(self.quantity),
            "unit_price": float(self.unit_price),
            "total_amount": self.total_amount,
        }


class LaborEntry(Base):
    """Labor entry for a daily entry - UPDATED: removed unique constraint to allow multiple employees per role"""

    __tablename__ = "labor_entries"
    # REMOVED: UniqueConstraint('daily_entry_id', 'labor_role_id', name='unique_entry_labor')
    # This allows multiple painters, supervisors, etc. per day

    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_entry_id = Column(
        Integer, ForeignKey("daily_entries.id", ondelete="CASCADE"), nullable=False
    )
    labor_role_id = Column(Integer, ForeignKey("labor_roles.id"), nullable=False)
    employee_name = Column(
        String(255), nullable=True
    )  # Optional but recommended for tracking
    regular_hours = Column(Numeric(10, 2), nullable=False, default=0)
    overtime_hours = Column(Numeric(10, 2), nullable=False, default=0)
    night_shift = Column(Boolean, default=False)  # Night shift differential

    # Relationships
    daily_entry = relationship("DailyEntry", back_populates="labor_entries")
    labor_role = relationship("LaborRole", back_populates="labor_entries")

    @property
    def total_amount(self):
        straight_rate = float(self.labor_role.straight_rate)
        overtime_rate = float(self.labor_role.overtime_rate)

        # Add night shift differential if applicable
        if self.night_shift:
            straight_rate += 2.00
            overtime_rate += 2.00

        regular_cost = float(self.regular_hours) * straight_rate
        overtime_cost = float(self.overtime_hours) * overtime_rate

        return regular_cost + overtime_cost

    def to_dict(self):
        return {
            "id": self.id,
            "labor_role_id": self.labor_role_id,
            "role_name": self.labor_role.name,
            "category": self.labor_role.category,
            "employee_name": self.employee_name,
            "regular_hours": float(self.regular_hours),
            "overtime_hours": float(self.overtime_hours),
            "night_shift": self.night_shift,
            "straight_rate": float(self.labor_role.straight_rate)
            + (2.00 if self.night_shift else 0),
            "overtime_rate": float(self.labor_role.overtime_rate)
            + (2.00 if self.night_shift else 0),
            "total_amount": self.total_amount,
        }


# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./tracktm.db"


def get_engine():
    """Get SQLAlchemy engine"""
    return create_engine(DATABASE_URL.replace("+aiosqlite", ""), echo=True)


def init_db():
    """Initialize database (create all tables)"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("✅ Database initialized successfully!")
    return engine


def get_session():
    """Get database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
