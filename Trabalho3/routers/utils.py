from fastapi import APIRouter, HTTPException
from models import Terreno, TerrenoBase, TerrenoPatch, Pessoa, Construcao, Obra
from typing import List, Dict, Type, TypedDict
from db import terrenos_collection, pessoas_collection, obras_collection, construcao_collection
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from logs import logging

class ModelMapEntry(TypedDict):
    type: Type
    collection: AsyncIOMotorCollection

map: Dict[str, ModelMapEntry] = {
    'terreno': {
        'type': Terreno,
        'collection': terrenos_collection
    },
    'pessoa': {
        'type': Pessoa,
        'collection': pessoas_collection
    },
    'construcao': {
        'type': Construcao,
        'collection': construcao_collection
    },
    'obra':{
        'type': Obra,
        'collection': obras_collection
    }
}

def validar_id(id:str):
    logging.info(f"Validação de id : {id}")
    try:
        obj_id = ObjectId(id)
    except InvalidId as e:
        logging.warning(f"Erro ao validar id : {e}")
        raise HTTPException(detail=f'ID {id} inválido', status_code=400)

async def quantidade_total_ocorrencias(tipo:str):
    return await map[tipo]['collection'].count_documents({})
 
async def listar(tipo:str):
    data = await map[tipo]['collection'].find().to_list()
    return [map[tipo]['type'].from_mongo(d) for d in data]

async def criar(tipo:str,data):
    result = await  map[tipo]['collection'].insert_one(data.model_dump())
    return str(result.inserted_id)

async def atualizar(tipo:str,id:str,data):
    validar_id(id)
    result = await map[tipo]['collection'].update_one({'_id':ObjectId(id)},{'$set':data.model_dump()})

    if result.modified_count != 1:
        raise HTTPException(detail=str(map[tipo]['type'].__name__)+' not found',status_code=404)
    
    data_atualizada =  await map[tipo]['collection'].find_one({'_id':ObjectId(id)})

    if data_atualizada is None:
        raise HTTPException(detail=str(map[tipo]['type'].__name__)+' not found',status_code=404)

    return map[tipo]['type'].from_mongo(data_atualizada)

async def deletar(tipo:str,id:str):
    validar_id(id)
    result = await map[tipo]['collection'].delete_one({'_id':ObjectId(id)})

    if result.deleted_count != 1:
        raise HTTPException(detail=str(map[tipo]['type'].__name__)+' not found',status_code=404)

    
    return {'msg':'deleted'}

async def patch(tipo:str,id:str,data):
    validar_id(id)
    update_data = data.model_dump(exclude_none=True)
    result = await map[tipo]['collection'].update_one({'_id':ObjectId(id)},{'$set':update_data})

    if result.modified_count != 1:
        raise HTTPException(detail=str(map[tipo]['type'].__name__)+' not found',status_code=404)
    
    data_atualizada =  await map[tipo]['collection'].find_one({'_id':ObjectId(id)})

    if data_atualizada is None:
        raise HTTPException(detail=str(map[tipo]['type'].__name__)+' not found',status_code=404)

    return map[tipo]['type'].from_mongo(data_atualizada)
