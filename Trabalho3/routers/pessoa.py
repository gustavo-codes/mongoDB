from fastapi import APIRouter, HTTPException
from models import Pessoa, PessoaBase, PessoaPatch
from typing import List
from db import pessoas_collection, terrenos_collection
from bson import ObjectId
from routers.utils import listar, criar, atualizar, deletar, patch,validar_id, quantidade_total_ocorrencias , paginacao , busca_parcial
from logs import logging
router = APIRouter(prefix='/pessoas', tags=['Pessoas'])

#Listar todos os usuários do banco
@router.get('/',response_model=List[Pessoa])
async def listar_pessoas():
    logging.info("ENDPOINT listar pessoas chamado")
    return await listar('pessoa')

#Quantidade total de usuarios
@router.get("/quantidade_usuarios")
async def quantidade_total_de_usuarios():
    logging.info("ENDPOINT listar quantidade de usuários chamado")
    try:
        total = await quantidade_total_ocorrencias('pessoa')
    except Exception as e:
        logging.info(f"Erro ao acessar o total de ocorrencias de usuário. Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao acessar o total de ocorrencias de usuário. Erro: {e}")
    return {"Quantidade":total}
#Paginação
@router.get('/paginacao')
async def paginacao_usuario(pagina: int = 1 , limite: int = 10):
    logging.info("ENDPOINT de paginacao chamado")
    return await paginacao('pessoa', pagina, limite)


#Filtro por atributo expecifico
@router.get("/filter/")
async def filtro(atributo:str, busca:str):
    return await busca_parcial('pessoa',atributo,busca)

#Adicionar uma nova pessoa no banco
@router.post('/')
async def criar_pessoa(pessoa:PessoaBase):
    logging.info(f"ENDPOINT criar pessoa chamado {pessoa}")
    return await criar('pessoa',pessoa)

#Adicionar um terreno a uma pesssoa
@router.post('/{pessoa_id}/adicionar-terreno/{terreno_id}')
async def adicionar_terreno_a_pessoa(pessoa_id:str,terreno_id:str):
    logging.info("ENDPOINT linkar terreno a pessoas chamado")
    
    validar_id(pessoa_id)
    validar_id(terreno_id)
    
    try:
        terreno = await terrenos_collection.find_one({'_id':ObjectId(terreno_id)})
    except Exception as e:
        logging.warning(f"Problema ao processar a busca por terreno de id {terreno_id}. Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Problema ao processar a busca por terreno de id {terreno_id}. Erro: {e}")
    
    try:
        pessoa = await pessoas_collection.find_one({'_id':ObjectId(pessoa_id)})
    except Exception as e:
        logging.warning(f"Problema ao processar busca por pessoa de id {pessoa_id}. Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Problema ao processar busca por pessoa de id {pessoa_id}. Erro: {e}")
    

    if terreno is None:
        logging.info(f"Terreno de id {terreno_id} não encontrado")
        raise HTTPException(detail='Terreno não encontrado',status_code=404)

    if pessoa is None:
        logging.info(f"Pessoa de id {pessoa_id} não encontrado")
        raise HTTPException(detail='Pessoa não encontrada',status_code=404)

    await terrenos_collection.update_one(
        {'_id':ObjectId(terreno_id)},
        {'$addToSet':{'pessoas_ids':ObjectId(pessoa_id)}}
    )

    await pessoas_collection.update_one(
        {'_id':ObjectId(pessoa_id)},
        {'$addToSet':{'terrenos_ids':ObjectId(terreno_id)}}
    )
    logging.info(f"Terreno de id {terreno_id} adicionado na lista de terrenos da pessoa de id {pessoa_id}")
    return {'msg':'Done'}

#Atualizar Pessoa
@router.put('/{pessoa_id}')
async def atualizar_pessoa(pessoa_id:str,pessoa:PessoaBase):
    logging.info(f"ENDPOINT atualizar pessoa chamado com o id {pessoa_id} e corpo {pessoa}")
    return await atualizar('pessoa',pessoa_id,pessoa)

@router.patch('/{pessoa_id}')
async def modificar_pessoa(pessoa_id:str,pessoa:PessoaPatch):
    return await patch('pessoa',pessoa_id,pessoa)

#Deletar pessoa
@router.delete('/{pessoa_id}')
async def deletar_pessoa(pessoa_id:str):
    logging.info(f"ENDPOINT de deletar pessoa chamado para pessoa de id {pessoa_id}")
    
    validar_id(pessoa_id)
    
    pessoa = await pessoas_collection.find_one({'_id':ObjectId(pessoa_id)})
    
    if not pessoa:
        logging.info(f"Pessoa de id {pessoa_id} não encontrada")
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    
    await terrenos_collection.update_many({'pessoas_ids':ObjectId(pessoa_id)},{'$pull':{'pessoas_ids':ObjectId(pessoa_id)}})
    return await deletar('pessoa',pessoa_id)