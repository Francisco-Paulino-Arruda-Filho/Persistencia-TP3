# app/routers/__init__.py
from .DepartmentRouter import router as department_router
from .EmployeeRouter import router as employee_router
from .BenefitRouter import router as benefit_router
from .EmployeeBenefitRouter import router as employee_benefit_router
from .PayrollRouter import router as payroll_router

__all__ = ["department_router", "employee_router", "benefit_router", "employee_benefit_router", "payroll_router"]
