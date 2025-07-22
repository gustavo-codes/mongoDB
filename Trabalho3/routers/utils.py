from fastapi import APIRouter, HTTPException
from models import Terreno, TerrenoBase, TerrenoPatch, Pessoa, Construcao, Obra
from typing import List, Dict, Type, TypedDict
from db import (
    terrenos_collection,
    pessoas_collection,
    obras_collection,
    construcao_collection,
)
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from logs import logging
import math


class ModelMapEntry(TypedDict):
    type: Type
    collection: AsyncIOMotorCollection


map: Dict[str, ModelMapEntry] = {
    "terreno": {"type": Terreno, "collection": terrenos_collection},
    "pessoa": {"type": Pessoa, "collection": pessoas_collection},
    "construcao": {"type": Construcao, "collection": construcao_collection},
    "obra": {"type": Obra, "collection": obras_collection},
}


def validar_id(id: str):
    """Valida se o id fornecido é um ObjectId válido."""
    logging.info(f"Validação de id : {id}")
    try:
        obj_id = ObjectId(id)
    except (InvalidId, Exception) as e:
        logging.warning(f"Erro ao validar id : {e}")
        raise HTTPException(status_code=400, detail=f"ID {id} inválido")


async def quantidade_total_ocorrencias(tipo: str):
    """Retorna a quantidade total de documentos do tipo informado."""
    try:
        return await map[tipo]["collection"].count_documents({})
    except Exception as e:
        logging.error(f"Erro ao contar documentos do tipo {tipo}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao contar documentos do tipo {tipo}.")


async def busca_parcial(tipo: str, campo: str, valor: str):
    """Busca parcial por campo e valor, com tratamento para campos string e numéricos."""
    logging.info(
        f"Busca parcial no tipo {tipo}, atributo buscado {campo}, valor passado {valor}"
    )
    try:
        # Saber se o campo existe no modelo
        if campo not in map[tipo]["type"].__fields__ and campo != "id":
            logging.warning(f"Campo {campo} não existe no modelo {tipo}")
            raise HTTPException(status_code=400, detail=f"Campo {campo} não existe no modelo {tipo}.")

        if campo == "id":
            logging.info("Campo procurado é um ID")
            validar_id(valor)
            data = await map[tipo]["collection"].find_one({"_id": ObjectId(valor)})
            if not data:
                logging.info(f"Nenhum registro encontrado para id {valor}")
                return None
            return map[tipo]["type"].from_mongo(data)

        # Tenta busca regex (string)
        filtro = {campo: {"$regex": valor, "$options": "i"}}
        data = await map[tipo]["collection"].find(filtro).to_list()
        if data:
            return [map[tipo]["type"].from_mongo(d) for d in data]

        # Se não encontrou, tenta busca numérica
        try:
            filtro = {campo: int(valor)}
            data = await map[tipo]["collection"].find(filtro).to_list()
            if data:
                return [map[tipo]["type"].from_mongo(d) for d in data]
        except Exception:
            logging.info(f"Valor {valor} não é numérico para campo {campo}")
        return []
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro na busca parcial: {e}")
        raise HTTPException(status_code=500, detail="Erro na busca parcial.")


async def paginacao(tipo: str, pagina: int = 1, limite: int = 10):
    if pagina < 1 or limite < 1:
        logging.info(
            "Paginação não foi concluida pois os valores de pagina ou limite são menores que 1"
        )
        raise HTTPException(
            status_code=400, detail="Valores precisam ser inteiros maiores que 0"
        )
    skip = (pagina - 1) * limite
    cursor = map[tipo]["collection"].find().skip(skip).limit(limite)
    data = await cursor.to_list(length=limite)
    to_return = [map[tipo]["type"].from_mongo(d) for d in data]
    total_paginas = math.ceil((await quantidade_total_ocorrencias(tipo)) / limite)
    return {"data": to_return, "pagina_atual": pagina, "total_paginas": total_paginas}


async def listar(tipo: str):
    logging.info("UTILS listar")
    try:
        data = await map[tipo]["collection"].find().to_list()
        return [map[tipo]["type"].from_mongo(d) for d in data]
    except Exception as e:
        logging.info(f"Erro ao listar atributos no utils. Error: {e}")
        raise HTTPException(status_code=400,detail=f"Erro ao listar atributos no utils. Error: {e}")


async def criar(tipo: str, data):
    result = await map[tipo]["collection"].insert_one(data.model_dump())
    return str(result.inserted_id)


async def atualizar(tipo: str, id: str, data):
    validar_id(id)
    result = await map[tipo]["collection"].update_one(
        {"_id": ObjectId(id)}, {"$set": data.model_dump()}
    )

    if result.modified_count != 1:
        raise HTTPException(
            detail=str(map[tipo]["type"].__name__) + " not found", status_code=404
        )

    data_atualizada = await map[tipo]["collection"].find_one({"_id": ObjectId(id)})

    if data_atualizada is None:
        raise HTTPException(
            detail=str(map[tipo]["type"].__name__) + " not found", status_code=404
        )

    return map[tipo]["type"].from_mongo(data_atualizada)


async def deletar(tipo: str, id: str):
    validar_id(id)
    result = await map[tipo]["collection"].delete_one({"_id": ObjectId(id)})

    if result.deleted_count != 1:
        raise HTTPException(
            detail=str(map[tipo]["type"].__name__) + " not found", status_code=404
        )

    return {"msg": "deleted"}


async def patch(tipo: str, id: str, data):
    validar_id(id)
    update_data = data.model_dump(exclude_none=True)
    result = await map[tipo]["collection"].update_one(
        {"_id": ObjectId(id)}, {"$set": update_data}
    )

    if result.modified_count != 1:
        raise HTTPException(
            detail=str(map[tipo]["type"].__name__) + " not found", status_code=404
        )

    data_atualizada = await map[tipo]["collection"].find_one({"_id": ObjectId(id)})

    if data_atualizada is None:
        raise HTTPException(
            detail=str(map[tipo]["type"].__name__) + " not found", status_code=404
        )

    return map[tipo]["type"].from_mongo(data_atualizada)
