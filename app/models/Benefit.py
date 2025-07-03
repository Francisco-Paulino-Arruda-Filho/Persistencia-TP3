from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from typing import TYPE_CHECKING

from app.models.PyObjectId import PyObjectId

if TYPE_CHECKING:
    from app.models.Benefit import BenefitBase  # se realmente necessário


class BenefitBase(BaseModel):
    name: str
    description: str
    value: float
    type: str  
    active: bool = True

class BenefitCreate(BenefitBase):
    pass

class BenefitOut(BenefitBase):
    id: Optional[PyObjectId] = Field(None, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        from_attributes = True  # Substitui orm_mode no Pydantic v2