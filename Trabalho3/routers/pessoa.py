from fastapi import APIRouter, HTTPException
from models import Pessoa, PessoaBase, PessoaPatch , Terreno
from typing import List
from db import pessoas_collection, terrenos_collection
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

router = APIRouter(prefix="/pessoas", tags=["Pessoas"])


# Listar todos os usuários do banco
@router.get("/", response_model=List[Pessoa])
async def listar_pessoas():
    """Lista todas as pessoas cadastradas."""
    logging.info("ENDPOINT listar pessoas chamado")
    try:
        pessoas = await listar("pessoa")
        return pessoas
    except Exception as e:
        logging.error(f"Erro ao listar pessoas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar pessoas.")


# Quantidade total de usuários
@router.get("/quantidade_usuarios")
async def quantidade_total_de_usuarios():
    """Retorna a quantidade total de pessoas cadastradas."""
    logging.info("ENDPOINT listar quantidade de usuários chamado")
    try:
        total = await quantidade_total_ocorrencias("pessoa")
        return {"quantidade": total}
    except Exception as e:
        logging.error(f"Erro ao acessar o total de ocorrencias de usuário. Erro: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao acessar o total de ocorrencias de usuário."
        )


# Paginação
@router.get("/paginacao")
async def paginacao_usuario(pagina: int = 1, limite: int = 10):
    """Retorna uma página de pessoas cadastradas."""
    logging.info(f"ENDPOINT de paginacao chamado - pagina: {pagina}, limite: {limite}")
    try:
        return await paginacao("pessoa", pagina, limite)
    except Exception as e:
        logging.error(f"Erro na paginação de pessoas: {e}")
        raise HTTPException(status_code=500, detail="Erro na paginação de pessoas.")


# Filtro por atributo específico
@router.get("/filter/")
async def filtro(atributo: str, busca: str):
    """Filtra pessoas por atributo específico."""
    logging.info(f"ENDPOINT de filtro chamado para atributo {atributo} e busca {busca}")
    if atributo not in Pessoa.model_fields:
        logging.warning(f"Atributo de filtro inválido: {atributo}")
        raise HTTPException(status_code=400, detail="Atributo de filtro inválido.")
    try:
        return await busca_parcial("pessoa", atributo, busca)
    except Exception as e:
        logging.error(f"Erro ao filtrar pessoas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao filtrar pessoas.")


#Todos os terrenos associados a uma id
@router.get("/terrenos/{pessoa_id}", response_model=List[Terreno])
async def terreno_associados_id(pessoa_id: str):
    """Lista todos os terrenos associados a uma pessoa pelo ID."""
    logging.info("ENDPOINT listar todos os terrenos associados a uma id")
    try:
        validar_id(pessoa_id)
        pessoa = await pessoas_collection.find_one({"_id": ObjectId(pessoa_id)})
        if not pessoa:
            logging.info(f"Pessoa de id : {pessoa_id} não encontrada.")
            raise HTTPException(status_code=404, detail=f"Pessoa de id : {pessoa_id} não encontrada.")
        terrenos = []
        for terreno_id in Pessoa.from_mongo(pessoa).terrenos_ids:
            terreno = await terrenos_collection.find_one({"_id": ObjectId(terreno_id)})
            if terreno:
                terrenos.append(Terreno.from_mongo(terreno))
        logging.info(terrenos)
        return terrenos
    except Exception as e:
        logging.error(f"Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar terrenos associados.")


# Adicionar uma nova pessoa no banco
@router.post("/", status_code=201)
async def criar_pessoa(pessoa: PessoaBase):
    """Adiciona uma nova pessoa ao banco de dados."""
    logging.info(f"ENDPOINT criar pessoa chamado {pessoa}")
    try:
        nova_pessoa = await criar("pessoa", pessoa)
        return {"message": "Pessoa criada com sucesso.", "data": nova_pessoa}
    except Exception as e:
        logging.error(f"Erro ao criar pessoa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar pessoa.")


# Adicionar um terreno a uma pessoa
@router.post("/{pessoa_id}/adicionar-terreno/{terreno_id}")
async def adicionar_terreno_a_pessoa(pessoa_id: str, terreno_id: str):
    """Adiciona um terreno à lista de terrenos de uma pessoa."""
    logging.info(
        f"ENDPOINT linkar terreno a pessoas chamado - pessoa_id: {pessoa_id}, terreno_id: {terreno_id}"
    )
    try:
        validar_id(pessoa_id)
        validar_id(terreno_id)
        terreno = await terrenos_collection.find_one({"_id": ObjectId(terreno_id)})
        pessoa = await pessoas_collection.find_one({"_id": ObjectId(pessoa_id)})
        if terreno is None:
            logging.info(f"Terreno de id {terreno_id} não encontrado")
            raise HTTPException(status_code=404, detail="Terreno não encontrado")
        if pessoa is None:
            logging.info(f"Pessoa de id {pessoa_id} não encontrada")
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")
        await terrenos_collection.update_one(
            {"_id": ObjectId(terreno_id)},
            {"$addToSet": {"pessoas_ids": ObjectId(pessoa_id)}},
        )
        await pessoas_collection.update_one(
            {"_id": ObjectId(pessoa_id)},
            {"$addToSet": {"terrenos_ids": ObjectId(terreno_id)}},
        )
        logging.info(
            f"Terreno de id {terreno_id} adicionado na lista de terrenos da pessoa de id {pessoa_id}"
        )
        return {"message": "Terreno adicionado à pessoa com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao adicionar terreno à pessoa: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao adicionar terreno à pessoa."
        )


# Atualizar Pessoa
@router.put("/{pessoa_id}")
async def atualizar_pessoa(pessoa_id: str, pessoa: PessoaBase):
    """Atualiza os dados de uma pessoa."""
    logging.info(
        f"ENDPOINT atualizar pessoa chamado com o id {pessoa_id} e corpo {pessoa}"
    )
    try:
        resultado = await atualizar("pessoa", pessoa_id, pessoa)
        return {"message": "Pessoa atualizada com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao atualizar pessoa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar pessoa.")


@router.patch("/{pessoa_id}")
async def modificar_pessoa(pessoa_id: str, pessoa: PessoaPatch):
    """Modifica parcialmente os dados de uma pessoa."""
    try:
        resultado = await patch("pessoa", pessoa_id, pessoa)
        return {"message": "Pessoa modificada com sucesso.", "data": resultado}
    except Exception as e:
        logging.error(f"Erro ao modificar pessoa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao modificar pessoa.")


# Deletar pessoa
@router.delete("/{pessoa_id}")
async def deletar_pessoa(pessoa_id: str):
    """Remove uma pessoa do banco de dados."""
    logging.info(f"ENDPOINT de deletar pessoa chamado para pessoa de id {pessoa_id}")
    try:
        validar_id(pessoa_id)
        pessoa = await pessoas_collection.find_one({"_id": ObjectId(pessoa_id)})
        if not pessoa:
            logging.info(f"Pessoa de id {pessoa_id} não encontrada")
            raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
        await terrenos_collection.update_many(
            {"pessoas_ids": ObjectId(pessoa_id)},
            {"$pull": {"pessoas_ids": ObjectId(pessoa_id)}},
        )
        await deletar("pessoa", pessoa_id)
        return {"message": "Pessoa deletada com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao deletar pessoa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar pessoa.")
