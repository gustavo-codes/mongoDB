from fastapi import APIRouter, HTTPException
from models import Terreno, TerrenoBase, TerrenoPatch, Construcao, Obra
from typing import List, Dict, Type, TypedDict
from db import (
    terrenos_collection,
    pessoas_collection,
    construcao_collection,
    obras_collection,
)
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from routers.utils import (
    listar,
    criar,
    atualizar,
    deletar,
    patch,
    quantidade_total_ocorrencias,
    paginacao,
    busca_parcial,
    validar_id,
)
from logs import logging

router = APIRouter(prefix="/terrenos", tags=["Terrenos"])


@router.get("/", response_model=List[Terreno])
async def listar_terrenos():
    logging.info("ENDPOINT listar terrenos chamado")
    try:
        return await listar("terreno")
    except Exception as e:
        logging.error(f"Erro ao listar terrenos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar terrenos.")


# Quantidade total de terrenos
@router.get("/quantidade_terrenos")
async def quantidade_total_de_terrenos():
    logging.info("ENDPOINT listar quantidade de terrenos chamado")
    try:
        total = await quantidade_total_ocorrencias("terreno")
        return {"quantidade": total}
    except Exception as e:
        logging.error(f"Erro ao acessar o total de terrenos: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao acessar o total de terrenos."
        )


# Quantidade gasto total em obras por terreno
@router.get("/terreno/gastos_obras/{terreno_id}")
async def gasto_obras_por_terreno(terreno_id: str):
    logging.info("ENDPOINT gasto total em obras por terreno")
    validar_id(terreno_id)
    try:
        terreno = await terrenos_collection.find_one({"_id": ObjectId(terreno_id)})
        if not terreno:
            logging.info(f"Terreno de id {terreno_id} não encontrado.")
            raise HTTPException(
                status_code=404, detail=f"Terreno de id {terreno_id} não encontrado."
            )

        terreno = Terreno.from_mongo(terreno)
        logging.info(f"Terreno encontrado: {terreno}")

        total_cost = 0
        for construcao_id in terreno.construcoes_ids:
            logging.info(f"Construção: {construcao_id}")
            construcao_doc = await construcao_collection.find_one({"_id": ObjectId(construcao_id)})
            if not construcao_doc:
                logging.warning(f"Construção de id {construcao_id} não encontrada.")
                continue
            construcao = Construcao.from_mongo(construcao_doc)
            for obra_id in construcao.obras_ids:
                obra_doc = await obras_collection.find_one({"_id": ObjectId(obra_id)})
                if not obra_doc:
                    logging.warning(f"Obra de id {obra_id} não encontrada.")
                    continue
                obra = Obra.from_mongo(obra_doc)
                total_cost += obra.custo
        return {"gasto_total": total_cost}

    except Exception as e:
        logging.error(f"Erro ao calcular gasto total em obras por terreno: {e}")
        raise HTTPException(status_code=500, detail="Erro ao calcular gasto total em obras por terreno.")


# Paginação
@router.get("/paginacao")
async def paginacao_terreno(pagina: int = 1, limite: int = 10):
    logging.info(f"ENDPOINT de paginação chamado - pagina: {pagina}, limite: {limite}")
    try:
        return await paginacao("terreno", pagina, limite)
    except Exception as e:
        logging.error(f"Erro na paginação de terrenos: {e}")
        raise HTTPException(status_code=500, detail="Erro na paginação de terrenos.")


# Filtro por atributo específico
@router.get("/filter/")
async def filtro(atributo: str, busca: str):
    logging.info(f"ENDPOINT de filtro chamado para atributo {atributo} e busca {busca}")
    if atributo not in Terreno.model_fields:
        logging.warning(f"Atributo de filtro inválido: {atributo}")
        raise HTTPException(status_code=400, detail="Atributo de filtro inválido.")
    try:
        return await busca_parcial("terreno", atributo, busca)
    except Exception as e:
        logging.error(f"Erro ao filtrar terrenos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao filtrar terrenos.")


@router.post("/")
async def criar_terreno(terreno: TerrenoBase):
    logging.info(f"ENDPOINT criar terreno chamado {terreno}")
    try:
        return await criar("terreno", terreno)
    except Exception as e:
        logging.error(f"Erro ao criar terreno: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar terreno.")


@router.put("/{terreno_id}")
async def atualizar_terreno(terreno_id: str, terreno: TerrenoBase):
    logging.info(
        f"ENDPOINT atualizar terreno chamado com o id {terreno_id} e corpo {terreno}"
    )
    try:
        resultado = await atualizar("terreno", terreno_id, terreno)
        return {"message": "Terreno atualizado com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao atualizar terreno: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar terreno.")


@router.patch("/{terreno_id}")
async def modificar_terreno(terreno_id: str, terreno: TerrenoPatch):
    try:
        resultado = await patch("terreno", terreno_id, terreno)
        return {"message": "Terreno modificado com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao modificar terreno: {e}")
        raise HTTPException(status_code=500, detail="Erro ao modificar terreno.")


# Ao deletar um terreno, atualiza a lista de terrenos_ids das pessoas que
# possuiam aquele terreno, além de deletar as contruções atreladas a ele
@router.delete("/{terreno_id}")
async def deletar_terreno(terreno_id: str):
    logging.info(f"ENDPOINT de deletar terreno chamado para terreno de id {terreno_id}")
    try:
        await construcao_collection.delete_many({"terreno_id": ObjectId(terreno_id)})
        await pessoas_collection.update_many(
            {"terrenos_ids": ObjectId(terreno_id)},
            {"$pull": {"terrenos_ids": ObjectId(terreno_id)}},
        )
        return await deletar("terreno", terreno_id)
    except Exception as e:
        logging.error(f"Erro ao deletar terreno: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar terreno.")
