from fastapi import APIRouter, HTTPException
from models import Construcao, ConstrucaoBase, ConstrucaoPatch
from typing import List
from db import construcao_collection, terrenos_collection
from bson import ObjectId
from routers.utils import listar, criar, atualizar, deletar, patch, validar_id
router = APIRouter(prefix='/contrucoes', tags=['Construções 🏘️'])

@router.get('/',response_model=List[Construcao])
async def listar_contrucoes():
    return await listar('construcao')

@router.post('/')
async def criar_construcao(construcao:ConstrucaoBase):
    validar_id(construcao.terreno_id)
    id = ObjectId(await criar('construcao',construcao))
    await construcao_collection.update_one({'_id':id},{'$set':{'terreno_id':ObjectId(construcao.terreno_id)}})
    await terrenos_collection.update_one(
        {'_id':ObjectId(construcao.terreno_id)},
        {'$addToSet':{'construcoes_ids':id}})
    return str(id)

@router.put('/{construcao_id}')
async def atualizar_construcao(construcao_id:str,construcao:ConstrucaoBase):
    return await atualizar('construcao',construcao_id,construcao)

@router.patch('/{construcao_id}')
async def modificar_construcao(construcao_id:str,construcao:ConstrucaoPatch):
    return await patch('construcao',construcao_id,construcao)


@router.delete('/{construcao_id}')
async def deletar_construcao(construcao_id:str):
    await deletar('construcao',construcao_id) #Deleta a construção
    
    #Retira da lista de construções do seu respectivo terreno
    await terrenos_collection.update_one({'construcoes_ids':ObjectId(construcao_id)},{'$pull':{'construcoes_ids':ObjectId(construcao_id)}})
    return {'msg':f'Construção {construcao_id} deletada'}