from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models.PyObjectId import PyObjectId

# Modelo base do Employee
class EmployeeBase(BaseModel):
    name: str
    cpf: str
    position: str
    admission_date: datetime
    department_id: Optional[str] = None  # Referência 1:N
    pay_rool_id: Optional[str] = None    # Referência 1:N
    benefits_id: List[str] = []          # Referência N:N

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
        "from_attributes": True
    }

# Modelo de criação: sem _id
class EmployeeCreate(EmployeeBase):
    pass

# Modelo de saída: inclui _id
class EmployeeOut(EmployeeBase):
    id: Optional[PyObjectId] = Field(None, alias="_id")

    model_config = {
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
        "from_attributes": True
    }
