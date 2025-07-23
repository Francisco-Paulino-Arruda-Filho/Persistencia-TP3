from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field
from app.models.PyObjectId import PyObjectId

class PayrollBase(BaseModel):
    employee_id: str  # N:1
    deductions: float
    discount: float
    net_salary: float
    reference_month: str  # YYYY-MM

class PayrollCreate(PayrollBase):
    pass

class PayrollOut(PayrollBase):
    id: Optional[PyObjectId] = Field(None, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class PayrollPaginated(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[PayrollOut]
