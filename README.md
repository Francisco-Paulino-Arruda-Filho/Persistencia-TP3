# 📊 Sistema de RH - API com FastAPI e SQLModel

Este projeto consiste em uma **API RESTful** para gerenciamento de um **Sistema de Recursos Humanos (RH)**, desenvolvida com **FastAPI** e **MongoDB**. O sistema permite o gerenciamento de departamentos, funcionários, folhas de pagamento, benefícios e vínculos entre funcionários e benefícios, incluindo filtros, paginação, contagens e muito mais.

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
- [MongoDB](https://www.mongodb.com/)

---

## ▶️ Como Executar

1. **Clone o repositório**:

   ```bash
   git clone https://github.com/seuusuario/sistema-rh.git
   ```

2. **Configure o banco de dados e variáveis de ambiente**:

   Crie um arquivo `.env` com o seguinte conteúdo:

   ```env
   MONGO_URL=mongodb://localhost:27017/
   ```

3. **Inicie o servidor**:

   ```bash
   uvicorn app.main:app --reload
   ```

---
