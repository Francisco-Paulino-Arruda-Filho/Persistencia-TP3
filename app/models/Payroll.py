from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.Employee import Employee

class PayrollBase(SQLModel):
    gross_salary: float
    deductions: float
    net_salary: float
    reference_month: str

class Payroll(PayrollBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(default=None, foreign_key="employee.id")

    employee: Optional["Employee"] = Relationship(back_populates="payrolls")

class PayrollCreate(PayrollBase):
    employee_id: int

class PayrollRead(PayrollBase):
    id: int

class PayrollUpdate(PayrollBase):
    gross_salary: Optional[float] = None
    deductions: Optional[float] = None
    net_salary: Optional[float] = None
    reference_month: Optional[str] = None
    employee_id: Optional[int] = None
