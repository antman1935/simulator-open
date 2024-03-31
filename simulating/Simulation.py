from simulating.SimObject import SimObject

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
    
    def setReferenceValue(self, ref_name, value):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        self.references[ref_name].set(value)

    def getReferenceValue(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name].get()
    
    def setReferences(self, mapping):
        for key, value in mapping.items():
            self.setReferenceValue(key, value)

    def getReferences(self, names):
        ret = {}
        for name in names:
            ret[name] = self.getReferenceValue(name)
        return ret
    
    def ref(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name]
    

