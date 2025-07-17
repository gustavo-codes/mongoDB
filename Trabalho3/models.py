from pydantic import BaseModel, Field, EmailStr, GetJsonSchemaHandler
from typing import List, Optional
from pydantic_core import core_schema
from bson import ObjectId
from datetime import datetime


class MongoModel(BaseModel):
    id: str

    @classmethod
    def from_mongo(cls, doc: dict):  # Converte ObjectId de _id em str
        doc = doc.copy()
        doc["id"] = str(doc["_id"])
        doc.pop("_id")

        # Alguns modelos contém atributos que vem do formato ObjectId
        # Então é preciso converte-los para str também
        if "construcoes_ids" in doc:
            doc["construcoes_ids"] = [str(c) for c in doc["construcoes_ids"]]

        if "terrenos_ids" in doc:
            doc["terrenos_ids"] = [str(t) for t in doc["terrenos_ids"]]

        if "pessoas_ids" in doc:
            doc["pessoas_ids"] = [str(p) for p in doc["pessoas_ids"]]

        if "terreno_id" in doc:
            doc["terreno_id"] = str(doc["terreno_id"])

        if "contrucao_id" in doc:
            doc["contrucao_id"] = str(doc["contrucao_id"])

        if "obras_ids" in doc:
            doc["obras_ids"] = [str(o) for o in doc["obras_ids"]]

        return cls(**doc)


class Endereco(BaseModel):
    rua: str
    numero: int
    cidade: str
    estado: str
    cep: str
    longitude: str
    latitude: str


class PessoaBase(BaseModel):
    nome: str
    email: EmailStr
    idade: int
    telefone: str
    profissao: str


class PessoaPatch(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    idade: Optional[int] = None
    telefone: Optional[str] = None
    profissao: Optional[str] = None


class Pessoa(PessoaBase, MongoModel):
    terrenos_ids: List[str] = []


class TerrenoBase(BaseModel):
    largura: float
    altua: float
    disponivel: bool
    preco: float
    descricao: str
    endereco: Endereco


class TerrenoPatch(BaseModel):
    largura: Optional[float] = None
    altua: Optional[float] = None
    disponivel: Optional[bool] = None
    preco: Optional[float] = None
    descricao: Optional[str] = None
    endereco: Optional[Endereco] = None


class Terreno(TerrenoBase, MongoModel):
    pessoas_ids: List[str] = []
    construcoes_ids: List[str] = []


class ConstrucaoBase(BaseModel):
    nome: str
    descricao: str
    custo_total: float
    tipo: str
    area: float
    terreno_id: str


class ConstrucaoPatch(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    custo_tota: Optional[float] = None
    tipo: Optional[str] = None
    area: Optional[float] = None


class Construcao(ConstrucaoBase, MongoModel):
    obras_ids: List[str]
    pass


class ObraBase(BaseModel):
    nome: str
    descricao: str
    inicio: datetime
    fim: Optional[datetime] = None
    custo: float
    contrucao_id: str


class ObraPatch(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    inicio: Optional[datetime] = None
    fim: Optional[datetime] = None
    custo: Optional[float] = None
    contrucao_id: Optional[str] = None


class Obra(ObraBase, MongoModel):
    pass
