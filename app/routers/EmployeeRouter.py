from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import Any, Dict, List
from ..logs.logger import logger
from ..core.db import employee_collection, benefit_collection, department_collection
from app.models.Employee import EmployeeCreate, EmployeeOut, PaginatedEmployeeResponse

router = APIRouter(prefix="/employees", tags=["Employees"])

def is_valid_objectid(id: str) -> bool:
    try:
        ObjectId(id)
        return True
    except Exception:
        return False


# 🔧 Utilitário para converter ObjectIds em strings
def fix_objectid(doc):
    if isinstance(doc, list):
        return [fix_objectid(i) for i in doc]
    if isinstance(doc, dict):
        out = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                out[k] = str(v)
            else:
                out[k] = fix_objectid(v)
        return out
    return doc

# 🔹 Utilitário para converter ID
def object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        logger.warning(f"ID inválido fornecido: {id_str}")
        raise HTTPException(status_code=400, detail="ID inválido")


@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate):
    # Valida department_id
    if employee.department_id:
        if not is_valid_objectid(employee.department_id):
            raise HTTPException(status_code=400, detail="ID de departamento inválido")
        department = await department_collection.find_one({"_id": ObjectId(employee.department_id)})
        if not department:
            raise HTTPException(status_code=404, detail="Departamento não encontrado")

    # Valida cada benefit_id
    for benefit_id in employee.benefits_id:
        if not is_valid_objectid(benefit_id):
            raise HTTPException(status_code=400, detail=f"ID de benefício inválido: {benefit_id}")
        if not await benefit_collection.find_one({"_id": ObjectId(benefit_id)}):
            raise HTTPException(status_code=404, detail=f"Benefício {benefit_id} não encontrado")

    new_employee = employee.model_dump()
    result = await employee_collection.insert_one(new_employee)

    # Atualiza department -> adiciona employee_id
    if employee.department_id:
        await department_collection.update_one(
            {"_id": ObjectId(employee.department_id)},
            {"$push": {"employee_ids": str(result.inserted_id)}}
        )

    created = await employee_collection.find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    return created


@router.get("/", response_model=PaginatedEmployeeResponse)
async def list_employees(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    logger.debug(f"Listando funcionários com skip={skip}, limit={limit}")
    try:
        total = await employee_collection.count_documents({})
        employees = await employee_collection.find().skip(skip).limit(limit).to_list(length=limit)
        for emp in employees:
            emp["_id"] = str(emp["_id"])
        logger.info(f"{len(employees)} funcionários encontrados")
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": employees
        }
    except Exception as e:
        logger.exception(f"Erro ao listar funcionários: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao listar funcionários")

@router.put("/{employee_id}", response_model=EmployeeOut)
async def update_employee(employee_id: str, employee: EmployeeCreate):
    if not is_valid_objectid(employee_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    existing = await employee_collection.find_one({"_id": ObjectId(employee_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    # Valida novo department_id
    if employee.department_id:
        if not is_valid_objectid(employee.department_id):
            raise HTTPException(status_code=400, detail="ID de departamento inválido")
        if not await department_collection.find_one({"_id": ObjectId(employee.department_id)}):
            raise HTTPException(status_code=404, detail="Departamento não encontrado")

    # Valida os benefit_ids
    for benefit_id in employee.benefits_id:
        if not is_valid_objectid(benefit_id):
            raise HTTPException(status_code=400, detail=f"ID de benefício inválido: {benefit_id}")
        if not await benefit_collection.find_one({"_id": ObjectId(benefit_id)}):
            raise HTTPException(status_code=404, detail=f"Benefício {benefit_id} não encontrado")

    # Atualiza departamento antigo (remove employee_id)
    if existing.get("department_id") and existing["department_id"] != employee.department_id:
        await department_collection.update_one(
            {"_id": ObjectId(existing["department_id"])},
            {"$pull": {"employee_ids": employee_id}}
        )

    # Atualiza departamento novo (adiciona employee_id)
    if employee.department_id and existing.get("department_id") != employee.department_id:
        await department_collection.update_one(
            {"_id": ObjectId(employee.department_id)},
            {"$addToSet": {"employee_ids": employee_id}}
        )

    await employee_collection.update_one(
        {"_id": ObjectId(employee_id)},
        {"$set": employee.dict()}
    )

    updated = await employee_collection.find_one({"_id": ObjectId(employee_id)})
    updated["_id"] = str(updated["_id"])
    return updated


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str):
    if not is_valid_objectid(employee_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    employee = await employee_collection.find_one({"_id": ObjectId(employee_id)})
    if not employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    # Remove referência no departamento
    if employee.get("department_id"):
        await department_collection.update_one(
            {"_id": ObjectId(employee["department_id"])},
            {"$pull": {"employee_ids": employee_id}}
        )

    await employee_collection.delete_one({"_id": ObjectId(employee_id)})

    
@router.get("/count", response_model=dict)
async def count_employees():
    try:
        count = await employee_collection.count_documents({})
        logger.info(f"Total de funcionários: {count}")
        return {"count": count}
    except Exception:
        logger.exception("Erro ao contar funcionários")
        raise HTTPException(status_code=500, detail="Erro interno ao contar funcionários")
    
@router.get("/get_by_admission_date", response_model=List[EmployeeOut])
async def get_by_admission_date(admission_date: datetime = Query(..., description="Data de admissão (AAAA-MM-DD)")):
    try:
        # Define intervalo do início ao fim do dia
        start_date = datetime(admission_date.year, admission_date.month, admission_date.day)
        end_date = start_date + timedelta(days=1)

        logger.debug(f"Buscando funcionários admitidos entre {start_date} e {end_date}")

        employees = await employee_collection.find({
            "admission_date": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).to_list(length=None)

        for emp in employees:
            emp["_id"] = str(emp["_id"])

        logger.info(f"{len(employees)} funcionários encontrados com data de admissão: {admission_date.date()}")
        return employees
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários por data de admissão {admission_date}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionários por data de admissão")
    
@router.get("get_by_cpf/{cpf}", response_model=EmployeeOut)
async def get_employee_by_cpf(cpf: str):
    logger.debug(f"Buscando funcionário por CPF {cpf}")
    try:
        employee = await employee_collection.find_one({"cpf": cpf})
        if not employee:
            logger.warning(f"Funcionário com CPF {cpf} não encontrado.")
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        employee["_id"] = str(employee["_id"])
        logger.info(f"Funcionário recuperado com sucesso: {employee}")
        return employee
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionário por CPF {cpf}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionário")
    
@router.get("/get_by_department/{department_id}", response_model=List[EmployeeOut])
async def get_by_department(department_id: str):
    logger.debug(f"Buscando funcionários no departamento {department_id}")
    try:
        employees = await employee_collection.find({"department_id": department_id}).to_list(length=None)

        for emp in employees:
            emp["_id"] = str(emp["_id"])

        if not employees:
            logger.warning(f"Nenhum funcionário encontrado no departamento {department_id}")
            raise HTTPException(status_code=404, detail="Nenhum funcionário encontrado nesse departamento")

        logger.info(f"{len(employees)} funcionários encontrados no departamento {department_id}")
        return employees

    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários por departamento {department_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionários por departamento")
    
@router.get("get_by_name/{name}", response_model=List[EmployeeOut])
async def get_by_name(name: str):
    logger.debug(f"Buscando funcionários com nome contendo '{name}'")
    try:
        employees = await employee_collection.find(
            {"name": {"$regex": name, "$options": "i"}}
        ).to_list(length=None)

        for emp in employees:
            emp["_id"] = str(emp["_id"])

        logger.info(f"{len(employees)} funcionários encontrados com nome '{name}'")
        return employees
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários por nome {name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionários por nome")
    
@router.get(
    "/benefits/{benefit_id}/departments/{department_id}/employees",
    response_model=List[Dict[str, Any]]
)

async def get_employees_by_benefit_and_department(benefit_id: str, department_id: str):
    try:
        
        if len(benefit_id) != 24 or len(department_id) != 24:
            logger.warning(f"ID inválido: benefício={benefit_id}, departamento={department_id}")
            raise HTTPException(status_code=400, detail="ID de benefício ou departamento inválido")

        if not await benefit_collection.find_one({"_id": benefit_id}):
            logger.warning(f"Benefício não encontrado: {benefit_id}")
            raise HTTPException(status_code=404, detail="Benefício não encontrado")

        if not await department_collection.find_one({"_id": department_id}):
            logger.warning(f"Departamento não encontrado: {department_id}")
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        
        employees = await employee_collection.find({
            "benefits_id": benefit_id,
            "department_id": department_id
        }).to_list(length=None)

        for emp in employees:
            emp["_id"] = str(emp["_id"])

        logger.info(f"{len(employees)} funcionários encontrados com benefício {benefit_id} no departamento {department_id}")
        return employees

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários com benefício {benefit_id} no departamento {department_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar funcionários")
    
@router.get("/get_by_benefit/{benefit_id}")
async def get_by_benefit(benefit_id: str):
    logger.debug(f"Buscando funcionários com benefício {benefit_id}")
    try:
        if not is_valid_objectid(benefit_id):
            raise HTTPException(status_code=400, detail="ID de benefício inválido")

        employees = await employee_collection.find({"benefits_id": benefit_id}).to_list(length=None)

        for emp in employees:
            emp["_id"] = str(emp["_id"])

        if not employees:
            logger.warning(f"Nenhum funcionário encontrado com benefício {benefit_id}")
            raise HTTPException(status_code=404, detail="Nenhum funcionário encontrado com esse benefício")

        logger.info(f"{len(employees)} funcionários encontrados com benefício {benefit_id}")
        return employees

    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários por benefício {benefit_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionários por benefício")

@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: str):
    try:
        oid = object_id(employee_id)
        employee = await employee_collection.find_one({"_id": oid})
        if not employee:
            logger.warning(f"Funcionário com ID {employee_id} não encontrado.")
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        employee["_id"] = str(employee["_id"])
        logger.info(f"Funcionário recuperado com sucesso: {employee}")
        return employee
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionário {employee_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionário")