from sqlalchemy import Column, String, Boolean, Integer, Float, Date, DateTime, ForeignKey, Text, JSON, Table
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
    email = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    opt_in_daily_reports = Column(Boolean, default=False)
    opt_in_tip_reports = Column(Boolean, default=False)

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
    display_order = Column(Integer, default=0)
    is_total = Column(Boolean, default=False)
    is_deduction = Column(Boolean, default=False)
    apply_to_revenue = Column(Boolean, default=False)
    revenue_is_deduction = Column(Boolean, default=False)
    apply_to_expense = Column(Boolean, default=False)
    expense_is_deduction = Column(Boolean, default=False)
    no_null_value = Column(Boolean, default=False)
    no_input = Column(Boolean, default=False)
    record_data = Column(Boolean, default=False)
    include_in_payroll_summary = Column(Boolean, default=False)

    positions = relationship(
        "Position",
        secondary=position_tip_requirements,
        back_populates="tip_requirements"
    )

class EmployeePositionSchedule(Base):
    __tablename__ = "employee_position_schedule"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id", ondelete="RESTRICT"), nullable=False)
    days_of_week = Column(JSON, default=list)

    employee = relationship("Employee", back_populates="position_schedules")
    position = relationship("Position")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    scheduled_days = Column(JSON, default=list)

    position = relationship("Position", back_populates="employees")
    position_schedules = relationship("EmployeePositionSchedule", back_populates="employee", cascade="all, delete-orphan")
    daily_entries = relationship("DailyEmployeeEntry", back_populates="employee")

    @property
    def display_name(self):
        """Return employee name in 'Last, First' format."""
        if self.last_name and self.first_name:
            return f"{self.last_name}, {self.first_name}"
        elif self.last_name:
            return self.last_name
        elif self.first_name:
            return self.first_name
        return self.name

class DailyBalance(Base):
    __tablename__ = "daily_balance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    day_of_week = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    finalized = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_source = Column(String, default="user")
    edited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    finalized_at = Column(DateTime, nullable=True)

    employee_entries = relationship("DailyEmployeeEntry", back_populates="daily_balance", cascade="all, delete-orphan")
    financial_line_items = relationship("DailyFinancialLineItem", back_populates="daily_balance", cascade="all, delete-orphan")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    edited_by_user = relationship("User", foreign_keys=[edited_by_user_id])

class DailyEmployeeEntry(Base):
    __tablename__ = "daily_employee_entries"

    id = Column(Integer, primary_key=True, index=True)
    daily_balance_id = Column(Integer, ForeignKey("daily_balance.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    tip_values = Column(JSON, default=dict)

    daily_balance = relationship("DailyBalance", back_populates="employee_entries")
    employee = relationship("Employee", back_populates="daily_entries")
    position = relationship("Position")

    def get_tip_value(self, field_name: str, default=0.0):
        if self.tip_values and isinstance(self.tip_values, dict):
            return self.tip_values.get(field_name, default)
        return default

class FinancialLineItemTemplate(Base):
    __tablename__ = "financial_line_item_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    display_order = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    is_deduction = Column(Boolean, default=False)
    is_starting_till = Column(Boolean, default=False)
    is_ending_till = Column(Boolean, default=False)

    daily_line_items = relationship("DailyFinancialLineItem", back_populates="template", cascade="all, delete-orphan")

class DailyFinancialLineItem(Base):
    __tablename__ = "daily_financial_line_items"

    id = Column(Integer, primary_key=True, index=True)
    daily_balance_id = Column(Integer, ForeignKey("daily_balance.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("financial_line_item_templates.id"), nullable=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    value = Column(Float, default=0.0)
    display_order = Column(Integer, default=0)
    is_employee_tip = Column(Boolean, default=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    daily_balance = relationship("DailyBalance", back_populates="financial_line_items")
    template = relationship("FinancialLineItemTemplate", back_populates="daily_line_items")
    employee = relationship("Employee")

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    schedule_type = Column(String, nullable=False)
    cron_expression = Column(String, nullable=True)
    interval_value = Column(Integer, nullable=True)
    interval_unit = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    date_range_type = Column(String, nullable=True)
    email_list = Column(String, nullable=True)
    bypass_opt_in = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    starts_at = Column(DateTime, nullable=True)

    employee = relationship("Employee")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")

class TaskExecution(Base):
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    result_data = Column(Text, nullable=True)

    task = relationship("ScheduledTask", back_populates="executions")
