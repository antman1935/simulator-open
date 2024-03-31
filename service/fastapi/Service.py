from fastapi import FastAPI
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
from typing_extensions import Annotated
import sys

simServer = None

class Settings(BaseSettings):
    SIM_ID: str
settings = Settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    from simulating.SimServer import SimulatorServer
    global simServer
    global settings
    print(settings.SIM_ID)
    simServer = SimulatorServer(settings.SIM_ID)
    yield
    simServer.stop()


app = FastAPI(lifespan=lifespan)

@app.get("/get/{query}")
async def get(query: Annotated[str, "Comma separated list of reference names to return."]):
    if query.strip() == "":
        return {}
    
    names = query.split(',')
    return await simServer.getReferences(names)

@app.get("/set/{query}")
async def set(query: Annotated[str, "'&' separated list of assignments in form ref_name=value."]):
    if query.strip() == "":
        return {}
    
    assignments = query.split('&')
    mapping = {}
    for assignment in assignments:
        [name, value] = assignment.split('=')
        mapping[name] = float(value)
    return await simServer.setReferences(mapping)