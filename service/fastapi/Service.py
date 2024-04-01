from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
from typing_extensions import Annotated
import inspect

simServer = None

def get_endpoint_parameters(attrs, default_value):
    # replace periods to guarantee names are valid python vars,
    # provide the mapping so that we can give the exact reference name
    # NOTE: Possible TODO - do something about names resolving to the same
    # alias. Issue is Ref_a100.Value and Ref.a100_Value both would have
    # Ref_a100_Value as the base parameter name. We have to avoid these collisions
    # manually or handle them explicitly.
    kwargs = {attr.replace('.', '_'): type_ for attr, type_ in attrs.items()}
    mapping = {attr.replace('.', '_'): attr for attr in attrs.keys()}
    params = [
        inspect.Parameter(
            param,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=type_,
            default=default_value
        ) for param, type_ in kwargs.items()
    ]

    return kwargs, mapping, params

def object_set_endpoint(object_name: str, attrs):
    kwargs, mapping, params = get_endpoint_parameters(attrs, None)

    async def endpoint(**kwargs):
        ref_settings = {f"{object_name}.{mapping[arg]}": kwargs[arg] for arg, val in kwargs.items() if val is not None}
        print(ref_settings)
        return await simServer.setReferences(ref_settings)
    
    endpoint.__signature__ = inspect.Signature(params)
    endpoint.__annotations__ = kwargs
    return endpoint

def create_object_set_endpoint(app: FastAPI, object_name: str, attrs: list[str]):
    endpoint_params = {
        attr: Annotated[float | None, Query(description=f"Set {object_name}'s internal field {attr}", alias=attr)] for attr in attrs
    }
    app.add_api_route(f"/{object_name}/set/", object_set_endpoint(object_name, endpoint_params), methods=["GET"])

def object_get_endpoint(object_name: str, attrs):
    kwargs, mapping, params = get_endpoint_parameters(attrs, True)

    async def endpoint(**kwargs):
        refs = [f"{object_name}.{mapping[arg]}" for arg, val in kwargs.items() if val]
        return await simServer.getReferences(refs)
    
    endpoint.__signature__ = inspect.Signature(params)
    endpoint.__annotations__ = kwargs
    return endpoint

def create_object_get_endpoint(app: FastAPI, object_name: str, attrs: list[str]):
    endpoint_params = {
        attr: Annotated[bool, Query(description=f"Set {attr} to False to exclude it from the returned values.", alias=attr)] for attr in attrs
    }
    app.add_api_route(f"/{object_name}/get/", object_get_endpoint(object_name, endpoint_params), methods=["GET"])

"""
This function queries the simulation for it's api and adds two endpoints for each object:
* object_name/get/...: for each reference from the object, have an optional boolean parameter to include the field in returned results
* object_name/set/...: for each writeable reference from the object, take an optional parameter to set the value.
"""
async def add_endpoints(app: FastAPI):
    api = await simServer.getAPI()
    for object, ref_dict in api.items():
        write_attrs = [ref_name for ref_name in ref_dict.keys() if not ref_dict[ref_name][0]]

        if len(write_attrs) > 0:
            create_object_set_endpoint(app, object, write_attrs)
        create_object_get_endpoint(app, object, [ref_name for ref_name in ref_dict.keys()])

class Settings(BaseSettings):
    SIM_ID: str
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from simulating.SimServer import SimulatorServer
    global simServer
    global settings
    simServer = SimulatorServer(settings.SIM_ID)
    await add_endpoints(app)
    yield
    simServer.stop()

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=422,
        content=exc.args,
    )

@app.get("/get/{query}")
async def get(query: Annotated[str, "Comma separated list of absolute reference names to return."]):
    if query.strip() == "":
        return {}
    
    names = query.split(',')
    return await simServer.getReferences(names)

@app.get("/set/{query}")
async def set(query: Annotated[str, "'&' separated list of assignments in form absolute_ref_name=value."]):
    if query.strip() == "":
        return {}
    
    assignments = query.split('&')
    mapping = {}
    for assignment in assignments:
        [name, value] = assignment.split('=')
        mapping[name] = float(value)
    return await simServer.setReferences(mapping)