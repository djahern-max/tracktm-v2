"""
Database Models - SQLAlchemy with SQLite
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, UniqueConstraint, create_engine
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
            "unit_price": float(self.unit_price)
        }


class DailyEntry(Base):
    """Daily timesheet entry (one per day per job)"""
    __tablename__ = "daily_entries"
    __table_args__ = (
        UniqueConstraint('job_number', 'entry_date', name='unique_job_date'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_number = Column(String(50), nullable=False)
    entry_date = Column(Date, nullable=False)
    
    # Relationship to line items
    line_items = relationship("EntryLineItem", back_populates="daily_entry", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "job_number": self.job_number,
            "entry_date": str(self.entry_date),
            "line_items": [item.to_dict() for item in self.line_items]
        }


class EntryLineItem(Base):
    """Individual material line item for a daily entry"""
    __tablename__ = "entry_line_items"
    __table_args__ = (
        UniqueConstraint('daily_entry_id', 'material_id', name='unique_entry_material'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_entry_id = Column(Integer, ForeignKey('daily_entries.id', ondelete='CASCADE'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
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
            "total_amount": self.total_amount
        }


# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./tracktm.db"

def get_engine():
    """Get SQLAlchemy engine"""
    return create_engine(DATABASE_URL.replace('+aiosqlite', ''), echo=True)

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
