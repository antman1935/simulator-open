from simulating.SimObject import SimObject
from enum import Enum

class ErrorType(Enum):
    INVALID_REFERENCE = 0
    READ_ONLY_FAILED_WRITE = 1
    MULTI_SET_FAILURE = 2

class SimulationError:
    def __init__(self, error_type: ErrorType, msg: str):
        self.error_type = error_type
        self.msg = msg

class Simulator:
    def __init__(self):
        self.objects = {}
        self.references = {}
        self.simulation_started = False

    def AddObject(self, object_name: str, object: SimObject):
        assert self.simulation_started == False, "All objects must be added before the simulation starts."
        assert object_name not in self.objects, f"'{object_name}' has already been used for another object."
        self.objects[object_name] = object
        for ref_name, ref in object.getReferences():
            fullname = object_name + '.' + ref_name
            self.references[fullname] = ref

        return object

    def step(self):
        if not self.simulation_started:
            self.simulation_started = True

        for object in self.objects.values():
            object.step()

        for _, object in self.objects.items():
            object.updateReferences()

    def getReferenceKeys(self):
        return self.references.keys()
    
    def setReferenceValue(self, ref_name, value) -> bool | SimulationError:
        if not ref_name in self.references:
            return SimulationError(ErrorType.INVALID_REFERENCE, f"'{ref_name}' does not exist.")
        if self.references[ref_name].read_only:
            return SimulationError(ErrorType.READ_ONLY_FAILED_WRITE, f"'{ref_name}' is read only!")
        self.references[ref_name].set(value)
        return True

    def getReferenceValue(self, ref_name) -> float | SimulationError:
        if not ref_name in self.references:
            return SimulationError(ErrorType.INVALID_REFERENCE, f"'{ref_name}' does not exist.")
        return self.references[ref_name].get()
    
    def setReferences(self, mapping) -> bool | SimulationError:
        return_errors = []
        for key, value in mapping.items():
            sub_ret = self.setReferenceValue(key, value)
            if isinstance(sub_ret, SimulationError):
                return_errors.append((key, str(sub_ret.error_type)))
        if len(return_errors) > 0:
            return SimulationError(ErrorType.MULTI_SET_FAILURE, f"The following references failed to be written: {return_errors}")
        return True

    def getReferences(self, names) -> dict[str, float] | SimulationError:
        ret = {}
        dne = []
        for name in names:
            ret[name] = self.getReferenceValue(name)
            if isinstance(ret[name], SimulationError):
                dne.append(name)
        if len(dne) > 0:
            return SimulationError(ErrorType.INVALID_REFERENCE, f"The following requested references do not exist: {', '.join(dne)}")
        return ret
    
    # not exposed on the webapi, crash if used improperly.
    def ref(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name]
    
    def getAPI(self):
        api = {}
        for obj_name, obj in self.objects.items():
            api[obj_name] = {}

            for (ref_name, ref) in obj.getReferences():
                api[obj_name][ref_name] = (ref.read_only, ref.min, ref.max)

        return api
    

