from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query
from app.core.db import employee_collection, benefit_collection, employee_benefit_collection
from app.logs.logger import logger
from app.models import EmployeeBenefitCreate, EmployeeBenefitOut
from app.models.EmployeeBenefit import EmployeeBenefitPaginated
from app.models.Benefit import BenefitOut

router = APIRouter(prefix="/employee_benefit", tags=["Employee Benefit"])

@router.post("/", response_model=EmployeeBenefitOut)
async def create_employee_benefit(employeeBenefit: EmployeeBenefitCreate):
    logger.debug("Criando benefício de funcionário")
    try:
        new_emp_benefit = employeeBenefit.model_dump(exclude_unset=True)

        emp = new_emp_benefit.get("employee_id")

        if emp:
            existing_emp = await employee_collection.find_one({"_id": ObjectId(emp)})
            if not existing_emp:
                logger.warning(f"Funcionário com ID {emp} não encontrado")
                raise HTTPException(status_code=404, detail="Funcionário não encontrada")

        benefit = new_emp_benefit.get("benefit_id")

        if benefit:
            existing_benefit = await benefit_collection.find_one({"_id": ObjectId(benefit)})
            if not existing_benefit:
                logger.warning(f"Benfício com ID {emp} não encontrado")
                raise HTTPException(status_code=404, detail="Benefício não encontrada")


        result = await employee_benefit_collection.insert_one(new_emp_benefit)
        created = await employee_benefit_collection.find_one({"_id": result.inserted_id})

        if created:
            created["_id"] = str(created["_id"])
            logger.info(f"Benefício de funcionário criado com sucesso: {created}")
            return created
        raise HTTPException(status_code=500, detail="Erro ao criar benefício de funcionário")

    except Exception as e:
        logger.exception(f"Erro ao criar benefício de funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar benefício de funcionário")


@router.get("/get_all", response_model=EmployeeBenefitPaginated)
async def list_employee_benefits(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    logger.debug(f"Listando benefícios de funcionário com skip={skip}, limit={limit}")
    try:
        total = await employee_benefit_collection.count_documents({})
        emp_benefits = await employee_benefit_collection.find().skip(skip).limit(limit).to_list(length=limit)

        for eb in emp_benefits:
            eb["_id"] = str(eb["_id"])

        logger.info("Retornando benefícios de funcionário com sucesso")

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": emp_benefits
        }
    except Exception as e:
        logger.exception(f"Erro ao listar os benefícios de funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar benefícios de funcionário")

@router.get("/count")
async def count_employee_benefits():
    try:
        count = await employee_benefit_collection.count_documents({})
        logger.info(f"Total de benefícios de funcionário: {count}")
        return {"count": count}
    except Exception as e:
        logger.exception(f"Erro ao contar os benefícios de funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao contar benefícios de funcionário")


@router.put("/{employee_benefit_id}", response_model=EmployeeBenefitOut)
async def update_employee_benefit(employee_benefit_id: str, payroll: EmployeeBenefitCreate):
    logger.debug(f"Atualizando benefícios de funcionário com o ID {employee_benefit_id}")

    try:
        oid = ObjectId(employee_benefit_id)
        update_eb = payroll.model_dump(exclude_unset=True)

        emp = update_eb.get("employee_id")

        if emp:
            existing_emp = await employee_collection.find_one({"_id": ObjectId(emp)})
            if not existing_emp:
                logger.warning(f"Funcionário com ID {emp} não encontrado")
                raise HTTPException(status_code=404, detail="Funcionário não encontrada")

        benefit = update_eb.get("benefit_id")

        if benefit:
            existing_benefit = await benefit_collection.find_one({"_id": ObjectId(benefit)})
            if not existing_benefit:
                logger.warning(f"Benfício com ID {emp} não encontrado")
                raise HTTPException(status_code=404, detail="Benefício não encontrada")

        result = await employee_benefit_collection.update_one({"_id": oid}, {"$set": update_eb})

        if result.matched_count == 0:
            logger.warning(f"Benefício de funcionário com ID {employee_benefit_id} não encontrada")
            raise HTTPException(status_code=404, detail="Benefício de funcionário não encontrada")

        updated = await employee_benefit_collection.find_one({"_id": oid})
        updated["_id"] = str(updated["_id"])

        logger.info(f"Benefício de funcionário com ID {employee_benefit_id} atualizada com sucesso")

        return updated

    except InvalidId:
        logger.warning(f"O ID {employee_benefit_id} não representa um benefício de funcionário")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao atualizar benefício de funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar benefício de funcionário")


@router.delete("/{employee_benefit_id}")
async def delete_employee_benefit(employee_benefit_id: str):
    logger.debug(f"Deletando benefícios de funcionário com o ID {employee_benefit_id}")

    try:
        oid = ObjectId(employee_benefit_id)
        result = await employee_benefit_collection.delete_one({"_id": oid})

        if result.deleted_count == 0:
            logger.warning(f"Benefício de funcionário com ID {employee_benefit_id} não encontrada para deleção")
            raise HTTPException(status_code=404, detail="Benefício de funcionário não encontrada")

        logger.info(f"Benefício de funcionário com ID {employee_benefit_id} deletada com sucesso")

        return {
            "detail": "Benefício de funcionário deletado com sucesso",
        }
    except InvalidId:
        logger.warning(f"O ID {employee_benefit_id} não representa um benefício de funcionário")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao deletar benefício de funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar benefício de funcionário")

@router.get("/active_benefits_by_employee_id")
async def get_active_benefits_by_employee_id(employee_id: str):
    cursor = employee_benefit_collection.find({"employee_id": employee_id})

    if not cursor:
        logger.warning(f"Funcionário com ID {employee_id} não encontrado")
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    employee_benefits = await cursor.to_list(length=None)
    results = []

    for eb in employee_benefits:
        benefit = await benefit_collection.find_one({"_id": ObjectId(eb.get("benefit_id")), "active": True})
        print(benefit)
        if benefit:
            results.append(benefit)

    return [BenefitOut(**doc) for doc in results]

@router.get("/{employee_benefit_id}", response_model=EmployeeBenefitOut)
async def get_employee_benefit(employee_benefit_id: str):
    logger.debug(f"Buscando benefícios de funcionário com o ID {employee_benefit_id}")

    try:
        oid = ObjectId(employee_benefit_id)

        empb = await employee_benefit_collection.find_one({"_id": oid})

        if not empb:
            logger.warning(f"benefícios de funcionário com o ID {employee_benefit_id} não encontrada")
            raise HTTPException(status_code=404, detail="benefícios de funcionário não encontrada")

        empb["_id"] = str(empb["_id"])
        return empb
    except InvalidId:
        logger.warning(f"O ID {employee_benefit_id} não representa um benefício de funcionário")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao buscar benefício de funcionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar benefício de funcionário")
