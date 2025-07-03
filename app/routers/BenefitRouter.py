from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import List
from ..core.db import benefit_collection
from ..logs.logger import logger
from app.models.Benefit import BenefitOut, BenefitCreate

router = APIRouter(prefix="/benefits", tags=["Benefits"])

# 🔹 Utilitário para validar e converter ObjectId
def object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        logger.warning(f"ID inválido fornecido: {id_str}")
        raise HTTPException(status_code=400, detail="ID inválido")

# 🔹 Listar benefícios com paginação
@router.get("/", response_model=List[BenefitOut])
async def list_benefits(skip: int = 0, limit: int = 10):
    try:
        logger.debug(f"Listando benefícios com skip={skip}, limit={limit}")
        benefits = await benefit_collection.find().skip(skip).limit(limit).to_list(length=limit)
        for benefit in benefits:
            benefit["_id"] = str(benefit["_id"])
        logger.info(f"{len(benefits)} benefícios listados com sucesso.")
        return benefits
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