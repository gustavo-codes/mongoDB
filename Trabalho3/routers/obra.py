from fastapi import APIRouter, HTTPException
from models import Obra, ObraBase, ObraPatch
from typing import List, Dict, Type, TypedDict
from db import terrenos_collection, pessoas_collection, construcao_collection
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from routers.utils import listar, criar, atualizar, deletar, patch, validar_id

router = APIRouter(prefix="/obras", tags=["Obras 🧱"])


@router.get("/", response_model=List[Obra])
async def listar_obras():
    return await listar("obra")


@router.post("/")
async def criar_obra(obra: ObraBase):
    validar_id(obra.contrucao_id)
    construcao = await construcao_collection.find_one(
        {"_id": ObjectId(obra.contrucao_id)}
    )
    if not construcao:
        raise HTTPException(detail="Contrução não existe", status_code=404)
    id = await criar("obra", obra)
    await construcao_collection.update_one(
        {"_id": ObjectId(obra.contrucao_id)}, {"$addToSet": {"obras_id": ObjectId(id)}}
    )
    return {"msg": "Done"}


@router.put("/")
async def atualizar_obra(obra_id: str, obra: ObraBase):
    return await atualizar("obra", obra_id, obra)


@router.patch("/")
async def modificar_obra(obra_id: str, obra: ObraPatch):
    return await patch("obra", obra_id, obra)


@router.delete("/")
async def deletar_obra(obra_id: str):
    await deletar("obra", obra_id)
    # Retira da lista de construções do seu respectivo terreno
    await construcao_collection.update_one(
        {"obras_ids": ObjectId(obra_id)}, {"$pull": {"obras_ids": ObjectId(obra_id)}}
    )
    return {"msg": f"Obra {obra_id} deletada"}
