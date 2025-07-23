from typing import Optional, List

from pydantic import BaseModel, Field

class EmployeeBenefitBase(BaseModel):
    employee_id: str
    benefit_id: str
    start_date: str
    end_date: Optional[str] = None
    custom_amount: Optional[float] = None


class EmployeeBenefitCreate(EmployeeBenefitBase):
    pass

class EmployeeBenefitOut(EmployeeBenefitBase):
    id: Optional[str] = Field(None, alias="_id")

    class Config:
        json_encoders = {str: str}  # Serializa strings como strings no JSON
        populate_by_name = True      # Permite que o alias (_id) seja populado por id
        orm_mode = True               # Permite que o modelo seja usado com ORMs

class EmployeeBenefitPaginated(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[EmployeeBenefitOut]