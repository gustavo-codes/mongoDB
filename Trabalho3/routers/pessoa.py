from fastapi import APIRouter, HTTPException
from models import Pessoa, PessoaBase, PessoaPatch
from typing import List
from db import pessoas_collection, terrenos_collection
from bson import ObjectId
from routers.utils import listar, criar, atualizar, deletar, patch
router = APIRouter(prefix='/pessoas', tags=['Pessoas🙍‍♂️'])

@router.get('/',response_model=List[Pessoa])

async def listar_pessoas():
    return await listar('pessoa')

@router.post('/')
async def criar_pessoa(pessoa:PessoaBase):
    return await criar('pessoa',pessoa)

@router.post('/{pessoa_id}/adicionar-terreno/{terreno_id}')
async def adicionar_terreno_a_pessoa(pessoa_id:str,terreno_id:str):
    terreno = await terrenos_collection.find_one({'_id':ObjectId(terreno_id)})
    pessoa = await pessoas_collection.find_one({'_id':ObjectId(pessoa_id)})

    if terreno is None:
        raise HTTPException(detail='Terreno não encontrado',status_code=404)

    if pessoa is None:
        raise HTTPException(detail='Pessoa não encontrada',status_code=404)

    await terrenos_collection.update_one(
        {'_id':ObjectId(terreno_id)},
        {'$addToSet':{'pessoas_ids':ObjectId(pessoa_id)}}
    )

    await pessoas_collection.update_one(
        {'_id':ObjectId(pessoa_id)},
        {'$addToSet':{'terrenos_ids':ObjectId(terreno_id)}}
    )

    return {'msg':'Done'}

@router.put('/{pessoa_id}')
async def atualizar_pessoa(pessoa_id:str,pessoa:PessoaBase):
    return await atualizar('pessoa',pessoa_id,pessoa)

@router.patch('/{pessoa_id}')
async def modificar_pessoa(pessoa_id:str,pessoa:PessoaPatch):
    return await patch('pessoa',pessoa_id,pessoa)

@router.delete('/{pessoa_id}')
async def deletar_pessoa(pessoa_id:str):
    await terrenos_collection.update_many({'pessoas_ids':ObjectId(pessoa_id)},{'$pull':{'pessoas_ids':ObjectId(pessoa_id)}})
    return await deletar('pessoa',pessoa_id)