from zlib import crc32
from enum import Enum
import sys, os
import pickle
import json

def deep_crc32(obj, depth = 0):
    ret = str(depth)
    if type(obj) is dict:
        for key in sorted(obj.keys()):
            ret = str(crc32(bytes(ret + key + str(deep_crc32(obj[key], depth + 1)), 'ascii')))
    elif type(obj) is list:
        for val in obj:
            ret = str(crc32(bytes(ret + str(deep_crc32(val, depth + 1)), 'ascii')))
    else:
        ret = str(crc32(bytes(ret + str(obj), 'ascii')))
    
    return ret

def check_distinct_keys(target, other):
    for key in other:
        if key in target:
            return key
    return None

# NOTE: You only have to do define a type if subclass is not abstract.
class ExportableType(Enum):
    Model = 0
    DataSource  = 1
    DataSet = 2

def relative_path_prefix(type: ExportableType):
    paths = {
        ExportableType.Model: 'modeling/hyperparameters',
        ExportableType.DataSource: 'modeling/datasource_configs',
        ExportableType.DataSet: 'modeling/dataset_configs',
    }
    if not type in paths.keys():
        raise Exception("Invalid ExportableType")
    return paths[type]

# guarantee the paths exist
if True:
    from pathlib import Path
    for e in ExportableType:
        Path(relative_path_prefix(e)).mkdir(parents=True, exist_ok=True)

"""
Represents a configuration object that can be exported to a pickle and reloaded
from the pickle file. Usually a subclass will be able to generate or load an
artifact based on this configuration object. It will also export the equivalent
configuration in json, so it is human readable.
Ex) ModelDefinition(Exportable) -> Model

This class gives each exportable a unique identifier in their subclass directory.
"""
class Exportable:


    def __init__(self):
        raise Exception("Abstract base class")
    
    """
    Each exportable subclass should have an enum defined and should
    override this method to return its associated enum.
    """
    def getExportType(self) -> ExportableType:
        raise Exception("Unimplemented")

    """
    Each subclass should override this and provide a human readable dictionary
    of parameters. This is used to generate a unique identifier.

    NOTE: subclasses should call super().export(), then add in their parameters
          and guaranteeing no name collisions.
    """
    def export_keys(self) -> list[dict]:
        return [{"__export_class__": str(self.getExportType())}]
    

    def export(self) -> dict:
        dicts = self.export_keys()
        cur = dicts[0]
        for i in range(1, len(dicts)):
            repeat = check_distinct_keys(cur, dicts[i])
            if not repeat is None:
                raise Exception(f"export parameter {repeat} repeated between class {str(type(self))} and its base class.")
            cur.update(dicts[i])
        return cur

    """
    Unique ID generation happens here. It takes the hash of all
    the parameters in the export in a deterministic way.
    """
    def exportableDescriptor(self) -> str:
        params = self.export()
        _hash1 = crc32(bytes(params["__export_class__"], 'ascii'))
        _hash2 = crc32(bytes(params["__export_class__"], 'ascii'))
        for key in sorted(params.keys()):
            if key == "__export_class__":
                continue
            inner = deep_crc32(params[key])
            _hash1 = crc32(bytes(str(_hash1) + key + inner, 'ascii'))
            _hash2 = crc32(bytes(str(_hash2) + inner, 'ascii'))

        return str(hex(_hash1))[2:] + "-" + str(hex(_hash2))[2:]
    
    """
    Save the exportable class in the class specific subdirectory.
    """
    def saveToFile(self, toJson = False):
        type = self.getExportType()
        id = self.exportableDescriptor()
        prefix = relative_path_prefix(type)
        path = f"{prefix}/{id}"


        assert not os.path.exists(path), f"exportable file of type {type} and id {id} already exists."

        with open(path, "wb+") as outfile:
            pickle.dump(self, outfile)

        if toJson:
            path_json = f"{path}.json"
            assert not os.path.exists(path_json), f"exportable file of type {type} and id {id} already exists (json)."
            with open(path_json, "w+") as outfile:
                json.dump(self.export(), outfile, indent=3, sort_keys=False)

    def fileAlreadyExists(self):
        type = self.getExportType()
        id = self.exportableDescriptor()
        prefix = relative_path_prefix(type)
        path = f"{prefix}/{id}"

        return os.path.exists(path)
    
    """
    Load the exportable class identified by the id from the class specific
    subdirectory.
    """
    def loadExportable(type: ExportableType, id: str):
        prefix = relative_path_prefix(type)
        path = f"{prefix}/{id}"
        if not os.path.exists(path):
            raise Exception(f"Exportable (type: {type}) specified by  {id} does not exist. Check subdir {prefix}")
        
        obj = None
        with open(path, "rb") as openfile:
            obj = pickle.load(openfile)

        return obj
