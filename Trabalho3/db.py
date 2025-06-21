import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

client = motor.motor_asyncio.AsyncIOMotorClient()

db = client['mydb2']

pessoas_collection = db['pessoas']
terrenos_collection = db['terrenos']
construcao_collection = db['construcao']
obras_collection = db['obras']