import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URL"))

database = client["rh"]

employee_collection = database["employees"]
department_collection = database["departments"]
benefit_collection = database["benefits"]
employee_benefit_collection = database["employee_benefits"]
payroll_collection = database["payrolls"]