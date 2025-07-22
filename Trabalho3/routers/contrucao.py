from fastapi import APIRouter, HTTPException
from models import Construcao, ConstrucaoBase, ConstrucaoPatch
from typing import List
from db import construcao_collection, terrenos_collection
from bson import ObjectId
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

router = APIRouter(prefix="/contrucoes", tags=["Construções"])


# Listar todas as construções
@router.get("/", response_model=List[Construcao])
async def listar_contrucoes():
    logging.info("ENDPOINT listar construções chamado")
    try:
        return await listar("construcao")
    except Exception as e:
        logging.error(f"Erro ao listar construções: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar construções.")


# Quantidade total de construções
@router.get("/quantidade_construcoes")
async def quantidade_total_de_construcoes():
    logging.info("ENDPOINT listar quantidade de construções chamado")
    try:
        total = await quantidade_total_ocorrencias("construcao")
        return {"quantidade": total}
    except Exception as e:
        logging.error(f"Erro ao acessar o total de construções: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao acessar o total de construções."
        )


# Paginação
@router.get("/paginacao")
async def paginacao_construcao(pagina: int = 1, limite: int = 10):
    logging.info(f"ENDPOINT de paginação chamado - pagina: {pagina}, limite: {limite}")
    try:
        return await paginacao("construcao", pagina, limite)
    except Exception as e:
        logging.error(f"Erro na paginação de construções: {e}")
        raise HTTPException(status_code=500, detail="Erro na paginação de construções.")


# Filtro por atributo específico
@router.get("/filter/")
async def filtro(atributo: str, busca: str):
    logging.info(f"ENDPOINT de filtro chamado para atributo {atributo} e busca {busca}")
    if atributo not in Construcao.model_fields:
        logging.warning(f"Atributo de filtro inválido: {atributo}")
        raise HTTPException(status_code=400, detail="Atributo de filtro inválido.")
    try:
        return await busca_parcial("construcao", atributo, busca)
    except Exception as e:
        logging.error(f"Erro ao filtrar construções: {e}")
        raise HTTPException(status_code=500, detail="Erro ao filtrar construções.")


@router.post("/")
async def criar_construcao(construcao: ConstrucaoBase):
    logging.info(f"ENDPOINT criar construção chamado {construcao}")
    try:
        validar_id(construcao.terreno_id)
        id = ObjectId(await criar("construcao", construcao))
        await construcao_collection.update_one(
            {"_id": id}, {"$set": {"terreno_id": ObjectId(construcao.terreno_id)}}
        )
        await terrenos_collection.update_one(
            {"_id": ObjectId(construcao.terreno_id)},
            {"$addToSet": {"construcoes_ids": id}},
        )
        return str(id)
    except Exception as e:
        logging.error(f"Erro ao criar construção: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar construção.")


@router.put("/{construcao_id}")
async def atualizar_construcao(construcao_id: str, construcao: ConstrucaoBase):
    logging.info(
        f"ENDPOINT atualizar construção chamado com o id {construcao_id} e corpo {construcao}"
    )
    try:
        resultado = await atualizar("construcao", construcao_id, construcao)
        return {"message": "Construção atualizada com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao atualizar construção: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar construção.")


@router.patch("/{construcao_id}")
async def modificar_construcao(construcao_id: str, construcao: ConstrucaoPatch):
    try:
        resultado = await patch("construcao", construcao_id, construcao)
        return {"message": "Construção modificada com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao modificar construção: {e}")
        raise HTTPException(status_code=500, detail="Erro ao modificar construção.")


@router.delete("/{construcao_id}")
async def deletar_construcao(construcao_id: str):
    logging.info(
        f"ENDPOINT de deletar construção chamado para construção de id {construcao_id}"
    )
    try:
        await deletar("construcao", construcao_id)  # Deleta a construção
        # Retira da lista de construções do seu respectivo terreno
        await terrenos_collection.update_one(
            {"construcoes_ids": ObjectId(construcao_id)},
            {"$pull": {"construcoes_ids": ObjectId(construcao_id)}},
        )
        return {"msg": f"Construção {construcao_id} deletada"}
    except Exception as e:
        logging.error(f"Erro ao deletar construção: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar construção.")
