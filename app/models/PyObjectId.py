from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId

# Tipo customizado para campos de ID do MongoDB (ObjectId)
class PyObjectId(ObjectId):
    # Integra o tipo ObjectId ao sistema de validação do Pydantic v2+
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Diz ao Pydantic para usar a função validate abaixo, sem infos extras
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        # Verifica se o valor recebido é um ObjectId válido
        if not ObjectId.is_valid(v):
            raise ValueError("ID inválido")
        return ObjectId(v)  # Retorna um ObjectId válido

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        # Garante que o OpenAPI/Swagger veja esse campo como string
        return {'type': 'string'}