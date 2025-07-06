from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import List

from app.models.Employee import EmployeeOut
from ..core.db import benefit_collection, employee_collection
from ..logs.logger import logger
from app.models.Benefit import BenefitOut, BenefitCreate, PaginatedBenefitResponse

router = APIRouter(prefix="/benefits", tags=["Benefits"])

# 🔹 Utilitário para validar e converter ObjectId
def object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        logger.warning(f"ID inválido fornecido: {id_str}")
        raise HTTPException(status_code=400, detail="ID inválido")

# 🔹 Listar benefícios com paginação
@router.get("/", response_model=PaginatedBenefitResponse)
async def list_benefits(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    try:
        logger.debug(f"Listando benefícios com skip={skip}, limit={limit}")
        total = await benefit_collection.count_documents({})
        benefits = await benefit_collection.find().skip(skip).limit(limit).to_list(length=limit)
        for benefit in benefits:
            benefit["_id"] = str(benefit["_id"])
        logger.info(f"{len(benefits)} benefícios listados com sucesso.")
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": benefits
        }
    except Exception as e:
        logger.exception(f"Erro ao listar benefícios: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar benefícios")

# 🔹 Criar benefício
@router.post("/", response_model=BenefitOut, status_code=status.HTTP_201_CREATED)
async def create_benefit(benefit: BenefitCreate):
    logger.debug(f"Tentando criar benefício: {benefit}")
    try:
        benefit_dict = benefit.model_dump(by_alias=True)
        result = await benefit_collection.insert_one(benefit_dict)
        created = await benefit_collection.find_one({"_id": result.inserted_id})
        if created:
            created["_id"] = str(created["_id"])
            logger.info(f"Benefício criado com sucesso: {created}")
            return created
        logger.error("Erro ao recuperar benefício após inserção.")
        raise HTTPException(status_code=500, detail="Erro ao criar benefício")
    except Exception as e:
        logger.exception(f"Erro ao criar benefício: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar benefício")

# 🔹 Atualizar benefício
@router.put("/{benefit_id}", response_model=BenefitOut)
async def update_benefit(benefit_id: str, update_data: BenefitCreate):
    logger.debug(f"Tentando atualizar benefício ID {benefit_id} com dados: {update_data}")
    try:
        oid = object_id(benefit_id)
        data = update_data.model_dump(by_alias=True)
        result = await benefit_collection.update_one({"_id": oid}, {"$set": data})

        if result.matched_count == 0:
            logger.warning(f"Benefício com ID {benefit_id} não encontrado para atualização.")
            raise HTTPException(status_code=404, detail="Benefício não encontrado")

        updated_benefit = await benefit_collection.find_one({"_id": oid})
        updated_benefit["_id"] = str(updated_benefit["_id"])
        logger.info(f"Benefício ID {benefit_id} atualizado com sucesso.")
        return updated_benefit
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao atualizar benefício ID {benefit_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar benefício")

# 🔹 Deletar benefício
@router.delete("/{benefit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_benefit(benefit_id: str):
    logger.debug(f"Tentando deletar benefício ID {benefit_id}")
    try:
        oid = object_id(benefit_id)
        result = await benefit_collection.delete_one({"_id": oid})
        if result.deleted_count == 0:
            logger.warning(f"Benefício com ID {benefit_id} não encontrado para deleção.")
            raise HTTPException(status_code=404, detail="Benefício não encontrado")

        logger.info(f"Benefício ID {benefit_id} deletado com sucesso.")
        return {"detail": "Benefício deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao deletar benefício ID {benefit_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar benefício")
    
@router.get("/count", response_model=dict)
async def count_benefits():
    try:
        count = await benefit_collection.count_documents({})
        logger.info(f"Total de benefícios: {count}")
        return {"count": count}
    except Exception:
        logger.exception("Erro ao contar benefícios")
        raise HTTPException(status_code=500, detail="Erro interno ao contar benefícios")
    
@router.get("/get_by_name", response_model=List[BenefitOut])
async def get_benefit_by_name(name: str):
    logger.debug(f"Buscando benefícios pelo nome: {name}")
    try:
        benefits = await benefit_collection.find({"name": {"$regex": name, "$options": "i"}}).to_list(length=100)
        if not benefits:
            logger.warning(f"Nenhum benefício encontrado com o nome: {name}")
            raise HTTPException(status_code=404, detail="Nenhum benefício encontrado")

        for benefit in benefits:
            benefit["_id"] = str(benefit["_id"])
        logger.info(f"{len(benefits)} benefícios encontrados com o nome: {name}")
        return benefits
    except Exception as e:
        logger.exception(f"Erro ao buscar benefícios pelo nome {name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefícios")
    

@router.get("/sort_by_value", response_model=List[BenefitOut])
async def sort_benefits_by_value(order: str = Query("asc", regex="^(asc|desc)$")):
    try:
        sort_order = 1 if order == "asc" else -1
        benefits = await benefit_collection.find().sort("value", sort_order).to_list(length=100)
        for benefit in benefits:
            benefit["_id"] = str(benefit["_id"])
        return benefits
    except Exception as e:
        logger.exception(f"Erro ao ordenar benefícios por valor: {e}")
        raise HTTPException(status_code=500, detail="Erro ao ordenar benefícios")

@router.get("/value_range", response_model=List[BenefitOut])
async def get_benefits_by_value_range(min_value: float, max_value: float):
    try:
        query = {"value": {"$gte": min_value, "$lte": max_value}}
        benefits = await benefit_collection.find(query).to_list(length=100)
        for benefit in benefits:
            benefit["_id"] = str(benefit["_id"])
        return benefits
    except Exception as e:
        logger.exception(f"Erro ao buscar benefícios por intervalo de valor: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefícios por intervalo de valor")

@router.get("/get/benefit_by_employee/{employee_id}", response_model=List[BenefitOut])
async def get_benefits_by_employee(employee_id: str):
    logger.debug(f"Buscando benefícios do funcionário {employee_id}")
    try:
        try:
            employee_oid = ObjectId(employee_id)
        except Exception:
            logger.warning(f"ID de funcionário inválido: {employee_id}")
            raise HTTPException(status_code=400, detail="ID de funcionário inválido")

        # Busca o funcionário
        employee = await employee_collection.find_one({"_id": employee_oid})
        if not employee:
            logger.warning(f"Funcionário {employee_id} não encontrado")
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")

        # Extrai e converte os IDs dos benefícios (se existirem)
        raw_benefit_ids = employee.get("benefits_id", [])
        benefit_ids = []
        for bid in raw_benefit_ids:
            try:
                benefit_ids.append(ObjectId(bid))
            except Exception:
                logger.warning(f"ID de benefício inválido encontrado no funcionário {employee_id}: {bid}")

        if not benefit_ids:
            logger.info(f"Funcionário {employee_id} não possui benefícios válidos")
            return []

        # Busca os benefícios no banco
        benefits = await benefit_collection.find({"_id": {"$in": benefit_ids}}).to_list(length=None)

        logger.info(f"{len(benefits)} benefícios encontrados para o funcionário {employee_id}")
        return benefits

    except Exception as e:
        logger.exception(f"Erro ao buscar benefícios do funcionário {employee_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefícios do funcionário")    

# 🔹 Buscar benefício por ID
@router.get("/{benefit_id}", response_model=BenefitOut)
async def get_benefit(benefit_id: str):
    logger.debug(f"Buscando benefício por ID {benefit_id}")
    try:
        oid = object_id(benefit_id)
        benefit = await benefit_collection.find_one({"_id": oid})
        if not benefit:
            logger.warning(f"Benefício com ID {benefit_id} não encontrado.")
            raise HTTPException(status_code=404, detail="Benefício não encontrado")

        benefit["_id"] = str(benefit["_id"])
        logger.info(f"Benefício recuperado com sucesso: {benefit}")
        return benefit
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao buscar benefício ID {benefit_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefício")
    
@router.get("/departments/{department_id}/benefits", response_model=List[BenefitOut])
async def get_department_benefits(department_id: str):
    try:
        employees = await employee_collection.find({"department_id": department_id}).to_list(length=None)
        benefit_ids = set()
        for emp in employees:
            benefit_ids.update(emp.get("benefits_id", []))

        if not benefit_ids:
            return []

        benefit_objects = await benefit_collection.find({"_id": {"$in": [ObjectId(bid) for bid in benefit_ids]}}).to_list(length=None)
        for b in benefit_objects:
            b["_id"] = str(b["_id"])
        return benefit_objects
    except Exception as e:
        logger.exception(f"Erro ao buscar benefícios do departamento {department_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefícios do departamento")
    
@router.get("/employees/many_benefits/{min_benefits}", response_model=List[EmployeeOut])
async def get_employees_with_many_benefits(min_benefits: int):
    try:
        employees = await employee_collection.find().to_list(length=None)
        result = [emp for emp in employees if len(emp.get("benefits_id", [])) >= min_benefits]
        for emp in result:
            emp["_id"] = str(emp["_id"])
        return result
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários com muitos benefícios: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar funcionários com muitos benefícios")
    
@router.get("/get_by_type", response_model=List[BenefitOut])
async def get_benefits_by_type(type: str):
    logger.debug(f"Buscando benefícios do tipo: {type}")
    try:
        benefits = await benefit_collection.find({"type": type}).to_list(length=100)
        if not benefits:
            logger.warning(f"Nenhum benefício encontrado do tipo: {type}")
            raise HTTPException(status_code=404, detail="Nenhum benefício encontrado")

        for benefit in benefits:
            benefit["_id"] = str(benefit["_id"])
        logger.info(f"{len(benefits)} benefícios encontrados do tipo: {type}")
        return benefits
    except Exception as e:
        logger.exception(f"Erro ao buscar benefícios do tipo {type}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefícios do tipo")