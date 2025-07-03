from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.Employee import EmployeeBase

class PayrollBase(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    employee_id: str  # N:1
    deductions: float
    discount: float
    net_salary: float
    reference_month: str  # YYYY-MM


class PayrollCreate(PayrollBase):
    pass

class PayrollOut(PayrollBase):
    employee: Optional["EmployeeBase"] = Relationship(back_populates="payrolls")

    class Config:
        orm_mode = True  # Permite que o modelo seja usado com ORMs
        json_encoders = {str: str}  # Serializa strings como strings no JSON
        populate_by_name = True  # Permite que o alias (_id) seja populado por id
