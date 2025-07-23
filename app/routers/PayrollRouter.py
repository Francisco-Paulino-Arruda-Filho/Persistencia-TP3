from typing import List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.util import await_fallback

from app.core.db import payroll_collection, employee_collection, department_collection
from app.logs.logger import logger
from app.models import PayrollOut, PayrollCreate
from app.models.Payroll import PayrollPaginated

router = APIRouter(prefix="/payroll", tags=["PayRolls"])

@router.post("/", response_model=PayrollOut, status_code=status.HTTP_201_CREATED)
async def create_payroll(payroll: PayrollCreate):
    logger.debug("Criando folha de pagamento")
    try:
        new_payroll = payroll.model_dump(exclude_unset=True)
        result = await payroll_collection.insert_one(new_payroll)
        created = await payroll_collection.find_one({"_id": result.inserted_id})

        if created:
            created["_id"] = str(created["_id"])
            logger.info(f"Folha de pagamento criada com sucesso: {created}")
            return created
        raise HTTPException(status_code=500, detail="Erro ao criar folha de pagamento")

    except Exception as e:
        logger.exception(f"Erro ao criar folha de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar folha de pagamento")

@router.get("/get_all", response_model=PayrollPaginated)
async def list_payrolls(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    logger.debug(f"Listando folhas de pagamento com skip={skip}, limit={limit}")
    try:
        total = await payroll_collection.count_documents({})
        payrolls = await payroll_collection.find().skip(skip).limit(limit).to_list(length=limit)

        for pr in payrolls:
            pr["_id"] = str(pr["_id"])

        logger.info("Retornando folhas de pagamento com sucesso")

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": payrolls
        }
    except Exception as e:
        logger.exception(f"Erro ao listar as folhas de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar folhas de pagamento")

@router.get("/count")
async def count_payrolls():
    try:
        count = await payroll_collection.count_documents({})
        logger.info(f"Total de folhas de pagamento: {count}")
        return {"count": count}
    except Exception as e:
        logger.exception(f"Erro ao contar as folhas de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao contar folhas de pagamento")

@router.put("/{payroll_id}", response_model=PayrollOut)
async def update_payroll(payroll_id: str, payroll: PayrollCreate):
    logger.debug(f"Atualizando folha de pagamento com o ID {payroll_id}")

    try:
        oid = ObjectId(payroll_id)
        update_pr = payroll.model_dump(exclude_unset=True)

        emp = update_pr.get("employee_id")

        if emp:
            existing_emp = await employee_collection.find_one({"_id": ObjectId(emp)})
            if not existing_emp:
                logger.warning(f"Funcionário com ID {emp} não encontrado")
                raise HTTPException(status_code=404, detail="Funcionário não encontrada")

        result = await payroll_collection.update_one({"_id": oid}, {"$set": update_pr})

        if result.matched_count == 0:
            logger.warning(f"Folha de pagamento com ID {payroll_id} não encontrada")
            raise HTTPException(status_code=404, detail="Folha de Pagamento não encontrada")

        updated = await payroll_collection.find_one({"_id": oid})
        updated["_id"] = str(updated["_id"])

        logger.info(f"Folha de Pagamento com ID {payroll_id} atualizada com sucesso")

        return updated

    except InvalidId:
        logger.warning(f"O ID {payroll_id} não representa uma folha de pagamento")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao atualizar folha de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar folha de pagamento")

@router.delete("/{payroll_id}")
async def delete_payroll(payroll_id: str):
    logger.debug(f"Deletando folha de pagamento com o ID {payroll_id}")

    try:
        oid = ObjectId(payroll_id)

        result_update = await employee_collection.update_many(
            {"pay_roll_id": payroll_id},
            {"$set": {"pay_roll_id": None}}
        )

        result_delete = await payroll_collection.delete_one({"_id": oid})

        if result_delete.deleted_count == 0:
            logger.warning(f"Folha de Pagamento com ID {payroll_id} não encontrada para deleção")
            raise HTTPException(status_code=404, detail="Folha de pagamento não encontrada")

        logger.info(f"Folha de pagamento com ID {payroll_id} deletada com sucesso")

        return {
            "detail": "Folha de pagamento deletada com sucesso",
            "employees_updated": result_update.modified_count
        }
    except InvalidId:
        logger.warning(f"O ID {payroll_id} não representa uma folha de pagamento")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao deletar folha de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar folha de pagamento")

@router.get("/get_by_department", response_model=List[PayrollOut])
async def get_payrolls_by_department(department_id: str):
    logger.debug(f"Buscando folhas de pagamento de funcionários do Departamento {department_id} ")

    try:
        department = await department_collection.find_one({"_id": ObjectId(department_id)})

        if not department:
            logger.warning(f"Departamento com o ID {department_id} não encontrado")
            raise HTTPException(status_code=404, detail="Departamento não encontrado")

        employees = []
        for emp_id in department.get("employee_ids"):
            emp = await employee_collection.find_one({"_id": ObjectId(emp_id)})
            employees.append(emp)

        payrolls = []
        for emp in employees:
            payroll = await payroll_collection.find_one({"employee_id": str(emp.get("_id"))})
            if payroll:
                payrolls.append(payroll)

        return payrolls
    except InvalidId:
        logger.warning(f"O ID {department_id} não representa um departamento")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao buscar folhas de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar folhaa de pagamento")

@router.get("/{payroll_id}", response_model=PayrollOut)
async def get_payroll(payroll_id: str):
    logger.debug(f"Buscando folha de pagamento com o ID {payroll_id}")

    try:
        oid = ObjectId(payroll_id)

        payroll = await payroll_collection.find_one({"_id": oid})

        if not payroll:
            logger.warning(f"Folha de pagamento com o ID {payroll_id} não encontrada")
            raise HTTPException(status_code=404, detail="Folha de pagamento não encontrada")

        payroll["_id"] = str(payroll["_id"])
        return payroll
    except InvalidId:
        logger.warning(f"O ID {payroll_id} não representa uma folha de pagamento")
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        logger.exception(f"Erro interno ao buscar folha de pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar folha de pagamento")