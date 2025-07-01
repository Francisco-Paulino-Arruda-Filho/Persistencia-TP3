# 📊 Sistema de RH - API com FastAPI e SQLModel

Este projeto consiste em uma **API RESTful** para gerenciamento de um **Sistema de Recursos Humanos (RH)**, desenvolvida com **FastAPI**, **SQLModel** e **Alembic**. O sistema permite o gerenciamento de departamentos, funcionários, folhas de pagamento, benefícios e vínculos entre funcionários e benefícios, incluindo filtros, paginação, contagens e muito mais.

---

## 📚 Funcionalidades

- CRUD completo para todas as entidades
- Relacionamentos:
  - 1:N entre **Departament** e **Employees**
  - 1:N entre **Employee** e **Payroll**
  - 1:1 entre **Departament** e **Employee**
  - N:N entre **Employee** e **Benefit**
- Paginação e filtros nos endpoints
- Consultas avançadas (texto parcial, data, relacionamentos)
- Migrações de banco com Alembic
- Registro de logs de operações

---

## 🧱 Entidades e Relacionamentos

### 🔹 Departamento
- `name`
- `location`
- `description`
- `extension`
- `manager`: relacionamento 1:1 com Funcionário  
- `Employees`: relacionamento 1:N com Funcionário

### 🔹 Funcionário
- `name`
- `cpf`
- `position`
- `admission_date`
- `departament_id`: relacionamento N:1 com Departamento
- `payroll`: relacionamento 1:N com FolhaPagamento  
- `benefits`: relacionamento N:N com Benefício (via tabela associativa)

### 🔹 Folha de Pagamento
- `employee_id`
- `deductions`
- `discount`
- `net_salary`
- `reference_month`

### 🔹 Benefício
- `name`
- `description`
- `value`
- `type`
- `active` (booleano)

### 🔹 FuncionárioBenefício (tabela associativa)
- `employee_id`
- `benefit_id`
- `start_date`
- `end_date`
- `custom_amount` (opcional)

---

## 🔧 Tecnologias Utilizadas

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [SQLite / PostgreSQL / MySQL] – compatível com todos
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)

---

## ▶️ Como Executar

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/seuusuario/sistema-rh.git
   ```

2. **Configure o banco de dados e variáveis de ambiente**:

   Crie um arquivo `.env` com o seguinte conteúdo:
   ```env
   DATABASE_URL=sqlite:///./rh.db
   ```

3. **Crie um arquivo alembic.ini na raiz do repositório**
   ```
   [alembic]
   script_location = %(here)s/alembic
   prepend_sys_path = .
   path_separator = os
   sqlalchemy.url = sqlalchemy.url = postgresql+psycopg2://user:SENHA@localhost:5432/rh

   [post_write_hooks]

   [loggers]
   keys = root,sqlalchemy,alembic

   [handlers]
   keys = console

   [formatters]
   keys = generic

   [logger_root]
   level = WARNING
   handlers = console
   qualname =

   [logger_sqlalchemy]
   level = WARNING
   handlers =
   qualname = sqlalchemy.engine

   [logger_alembic]
   level = INFO
   handlers =
   qualname = alembic

   [handler_console]
   class = StreamHandler
   args = (sys.stderr,)
   level = NOTSET
   formatter = generic

   [formatter_generic]
   format = %(levelname)-5.5s [%(name)s] %(message)s
   datefmt = %H:%M:%S
   ```

4. **Execute o comando**
   ```bash
   alembic revision --autogenerate -m "Migracao inicial"
   ```

5. **Execute as migrações Alembic**:
   ```bash
   alembic upgrade head
   ```

6. **Inicie o servidor**:
   ```bash
   uvicorn app.main:app --reload
   ```

---
