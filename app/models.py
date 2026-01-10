from sqlalchemy import Column, String, Boolean, Integer, Float, Date, ForeignKey, Text, JSON, Table
from sqlalchemy.orm import relationship
from app.database import Base

position_tip_requirements = Table(
    'position_tip_requirements',
    Base.metadata,
    Column('position_id', Integer, ForeignKey('positions.id'), primary_key=True),
    Column('tip_requirement_id', Integer, ForeignKey('tip_entry_requirements.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    is_admin = Column(Boolean, default=False)

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)

    employees = relationship("Employee", back_populates="position")
    tip_requirements = relationship(
        "TipEntryRequirement",
        secondary=position_tip_requirements,
        back_populates="positions"
    )

class TipEntryRequirement(Base):
    __tablename__ = "tip_entry_requirements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    field_name = Column(String, unique=True, nullable=False)

    positions = relationship(
        "Position",
        secondary=position_tip_requirements,
        back_populates="tip_requirements"
    )

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    scheduled_days = Column(JSON, default=list)

    position = relationship("Position", back_populates="employees")
    daily_entries = relationship("DailyEmployeeEntry", back_populates="employee")

class DailyBalance(Base):
    __tablename__ = "daily_balance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    day_of_week = Column(String, nullable=False)
    total_cash_sales = Column(Float, default=0.0)
    total_card_sales = Column(Float, default=0.0)
    total_tips_collected = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    finalized = Column(Boolean, default=False)

    employee_entries = relationship("DailyEmployeeEntry", back_populates="daily_balance", cascade="all, delete-orphan")

class DailyEmployeeEntry(Base):
    __tablename__ = "daily_employee_entries"

    id = Column(Integer, primary_key=True, index=True)
    daily_balance_id = Column(Integer, ForeignKey("daily_balance.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    bank_card_sales = Column(Float, default=0.0)
    bank_card_tips = Column(Float, default=0.0)
    cash_tips = Column(Float, default=0.0)
    total_sales = Column(Float, default=0.0)
    adjustments = Column(Float, default=0.0)
    calculated_take_home = Column(Float, default=0.0)

    daily_balance = relationship("DailyBalance", back_populates="employee_entries")
    employee = relationship("Employee", back_populates="daily_entries")
