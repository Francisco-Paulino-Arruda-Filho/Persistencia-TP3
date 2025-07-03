from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.PyObjectId import PyObjectId


"""
from app.models.Employee import EmployeeRead

if TYPE_CHECKING:
    from app.models.Employee import Employee
employees: List[EmployeeRead] = []
    manager: EmployeeRead = None
"""

class DepartmentBase(BaseModel):
    name: str
    location: str
    description: str
    extension: str
    employee_ids: List[str] = []
    manager_id: Optional[str] = None

# Modelo de criação: sem _id
class DepartmentCreate(DepartmentBase):
    pass

# Modelo de leitura: inclui _id como PyObjectId
class DepartmentOut(DepartmentBase):
    id: Optional[PyObjectId] = Field(None, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class PaginatedDepartmentResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[DepartmentOut]