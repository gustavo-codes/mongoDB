from fastapi import APIRouter, HTTPException
from models import Terreno, TerrenoBase, TerrenoPatch, Construcao
from typing import List, Dict, Type, TypedDict
from db import terrenos_collection, pessoas_collection, construcao_collection
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from routers.utils import listar, criar, atualizar, deletar, patch

router = APIRouter(prefix='/terrenos', tags=['Terenos 🏕️'])


@router.get('/',response_model=List[Terreno])
async def listar_terrenos():
    return await listar('terreno')
   
@router.post('/')
async def criar_terreno(terreno:TerrenoBase):
    return await criar('terreno',terreno)

@router.put('/{terreno_id}')
async def atualizar_terreno(terreno_id:str,terreno:TerrenoBase):
    return await atualizar('terreno',terreno_id,terreno)

@router.patch('/{terreno_id}')
async def modificar_terreno(terreno_id:str,terreno:TerrenoPatch):
    return await patch('terreno',terreno_id,terreno)

#Ao deletar um terreno, atualiza a lista de terrenos_ids das pessoas que
#possuiam aquele terreno, além de deletar as contruções atreladas a ele
@router.delete('/{terreno_id}')
async def deletar_terreno(terreno_id:str):
    await construcao_collection.delete_many({'terreno_id':ObjectId(terreno_id)})
    await pessoas_collection.update_many({'terrenos_ids':ObjectId(terreno_id)},{'$pull':{'terrenos_ids':ObjectId(terreno_id)}})
    return await deletar('terreno',terreno_id)
   