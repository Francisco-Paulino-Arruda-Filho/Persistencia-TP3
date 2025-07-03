from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import List
from ..logs.logger import logger
from ..core.db import employee_collection
from app.models.Employee import EmployeeCreate, EmployeeOut

router = APIRouter(prefix="/employees", tags=["Employees"])


# 🔹 Utilitário para converter ID
def object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        logger.warning(f"ID inválido fornecido: {id_str}")
        raise HTTPException(status_code=400, detail="ID inválido")


# 🔹 Criar funcionário
@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate):
    logger.debug(f"Tentando criar funcionário: {employee}")
    try:
        employee_dict = employee.model_dump(exclude_unset=True)
        result = await employee_collection.insert_one(employee_dict)
        created = await employee_collection.find_one({"_id": result.inserted_id})
        if created:
            created["_id"] = str(created["_id"])
            logger.info(f"Funcionário criado com sucesso: {created}")
            return created
        logger.error("Erro ao recuperar funcionário após inserção")
        raise HTTPException(status_code=500, detail="Erro ao criar funcionário")
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar funcionário")


# 🔹 Listar todos os funcionários
@router.get("/", response_model=List[EmployeeOut])
async def list_employees():
    try:
        logger.debug("Listando todos os funcionários.")
        employees = await employee_collection.find().to_list(length=None)
        for emp in employees:
            emp["_id"] = str(emp["_id"])
        logger.info(f"{len(employees)} funcionários encontrados.")
        return employees
    except Exception as e:
        logger.exception(f"Erro ao listar funcionários: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar funcionários")

# 🔹 Atualizar funcionário
@router.put("/{employee_id}", response_model=EmployeeOut)
async def update_employee(employee_id: str, update_data: EmployeeCreate):
    logger.debug(f"Tentando atualizar funcionário ID {employee_id} com dados {update_data}")
    try:
        data = update_data.model_dump(by_alias=True, exclude_unset=True)
        result = await employee_collection.update_one(
            {"_id": object_id(employee_id)},
            {"$set": data}
        )
        if result.matched_count == 0:
            logger.warning(f"Funcionário ID {employee_id} não encontrado para atualização.")
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        data["_id"] = employee_id
        logger.info(f"Funcionário ID {employee_id} atualizado com sucesso.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao atualizar funcionário {employee_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar funcionário")


# 🔹 Deletar funcionário
@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str):
    logger.debug(f"Tentando deletar funcionário ID {employee_id}")
    try:
        oid = object_id(employee_id)
        result = await employee_collection.delete_one({"_id": oid})
        if result.deleted_count == 0:
            logger.warning(f"Funcionário ID {employee_id} não encontrado para deleção.")
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        logger.info(f"Funcionário ID {employee_id} deletado com sucesso.")
        return {"detail": "Funcionário deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao deletar funcionário {employee_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar funcionário")
    
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
    
# 🔹 Buscar funcionário por ID
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