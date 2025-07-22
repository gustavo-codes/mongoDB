from fastapi import APIRouter, HTTPException
from models import Obra, ObraBase, ObraPatch
from typing import List, Dict, Type, TypedDict
from db import terrenos_collection, pessoas_collection, construcao_collection
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from routers.utils import (
    listar,
    criar,
    atualizar,
    deletar,
    patch,
    validar_id,
    quantidade_total_ocorrencias,
    paginacao,
    busca_parcial,
)
from logs import logging

router = APIRouter(prefix="/obras", tags=["Obras 🧱"])


# Listar todas as obras
@router.get("/", response_model=List[Obra])
async def listar_obras():
    logging.info("ENDPOINT listar obras chamado")
    try:
        return await listar("obra")
    except Exception as e:
        logging.error(f"Erro ao listar obras: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar obras.")


# Quantidade total de obras
@router.get("/quantidade_obras")
async def quantidade_total_de_obras():
    logging.info("ENDPOINT listar quantidade de obras chamado")
    try:
        total = await quantidade_total_ocorrencias("obra")
        return {"quantidade": total}
    except Exception as e:
        logging.error(f"Erro ao acessar o total de obras: {e}")
        raise HTTPException(status_code=500, detail="Erro ao acessar o total de obras.")


# Paginação
@router.get("/paginacao")
async def paginacao_obra(pagina: int = 1, limite: int = 10):
    logging.info(f"ENDPOINT de paginação chamado - pagina: {pagina}, limite: {limite}")
    try:
        return await paginacao("obra", pagina, limite)
    except Exception as e:
        logging.error(f"Erro na paginação de obras: {e}")
        raise HTTPException(status_code=500, detail="Erro na paginação de obras.")


# Filtro por atributo específico
@router.get("/filter/")
async def filtro(atributo: str, busca: str):
    logging.info(f"ENDPOINT de filtro chamado para atributo {atributo} e busca {busca}")
    if atributo not in Obra.model_fields:
        logging.warning(f"Atributo de filtro inválido: {atributo}")
        raise HTTPException(status_code=400, detail="Atributo de filtro inválido.")
    try:
        return await busca_parcial("obra", atributo, busca)
    except Exception as e:
        logging.error(f"Erro ao filtrar obras: {e}")
        raise HTTPException(status_code=500, detail="Erro ao filtrar obras.")


@router.post("/")
async def criar_obra(obra: ObraBase):
    logging.info(f"ENDPOINT criar obra chamado {obra}")
    try:
        validar_id(obra.contrucao_id)
        construcao = await construcao_collection.find_one(
            {"_id": ObjectId(obra.contrucao_id)}
        )
        if not construcao:
            logging.info(f"Construção de id {obra.contrucao_id} não encontrada")
            raise HTTPException(detail="Construção não existe", status_code=404)
        id = await criar("obra", obra)
        await construcao_collection.update_one(
            {"_id": ObjectId(obra.contrucao_id)},
            {"$addToSet": {"obras_id": ObjectId(id)}},
        )
        return {"msg": "Done"}
    except Exception as e:
        logging.error(f"Erro ao criar obra: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar obra.")


@router.put("/")
async def atualizar_obra(obra_id: str, obra: ObraBase):
    logging.info(f"ENDPOINT atualizar obra chamado com o id {obra_id} e corpo {obra}")
    try:
        resultado = await atualizar("obra", obra_id, obra)
        return {"message": "Obra atualizada com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao atualizar obra: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar obra.")


@router.patch("/")
async def modificar_obra(obra_id: str, obra: ObraPatch):
    try:
        resultado = await patch("obra", obra_id, obra)
        return {"message": "Obra modificada com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao modificar obra: {e}")
        raise HTTPException(status_code=500, detail="Erro ao modificar obra.")


@router.delete("/")
async def deletar_obra(obra_id: str):
    logging.info(f"ENDPOINT de deletar obra chamado para obra de id {obra_id}")
    try:
        await deletar("obra", obra_id)
        await construcao_collection.update_one(
            {"obras_ids": ObjectId(obra_id)},
            {"$pull": {"obras_ids": ObjectId(obra_id)}},
        )
        return {"msg": f"Obra {obra_id} deletada"}
    except Exception as e:
        logging.error(f"Erro ao deletar obra: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar obra.")
