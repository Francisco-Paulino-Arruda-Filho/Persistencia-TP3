from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import Any, Dict, List
from ..logs.logger import logger
from ..core.db import employee_collection, benefit_collection, department_collection
from app.models.Employee import EmployeeCreate, EmployeeOut, PaginatedEmployeeResponse

router = APIRouter(prefix="/employees", tags=["Employees"])

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
    
@router.get("/benefits/{benefit_id}/departments/{department_id}/employees", response_model=List[Dict[str, Any]])
async def get_employees_by_benefit_and_department(benefit_id: str, department_id: str):
    try:
        # Converte os IDs
        try:
            benefit_oid = ObjectId(benefit_id)
            department_oid = ObjectId(department_id)
        except Exception:
            logger.warning(f"ID inválido fornecido: benefício={benefit_id}, departamento={department_id}")
            raise HTTPException(status_code=400, detail="ID de benefício ou departamento inválido")

        # Verifica se o benefício existe
        benefit = await benefit_collection.find_one({"_id": benefit_oid})
        if not benefit:
            logger.warning(f"Benefício não encontrado: {benefit_id}")
            raise HTTPException(status_code=404, detail="Benefício não encontrado")

        # Verifica se o departamento existe
        department = await department_collection.find_one({"_id": department_oid})
        if not department:
            logger.warning(f"Departamento não encontrado: {department_id}")
            raise HTTPException(status_code=404, detail="Departamento não encontrado")

        # Busca funcionários com o benefício e pertencentes ao departamento
        employees_cursor = employee_collection.find({
            "benefits_id": benefit_oid,
            "department_id": department_oid  # Agora sim: ObjectId
        })
        employees = await employees_cursor.to_list(length=None)
        employees = fix_objectid(employees)

        logger.info(f"{len(employees)} funcionários encontrados com benefício {benefit_id} no departamento {department_id}")
        return [
            {
                "benefit": fix_objectid(benefit),
                "department": fix_objectid(department),
                "employee": emp
            }
            for emp in employees
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários com benefício {benefit_id} no departamento {department_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionários com benefício e departamento")
    
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