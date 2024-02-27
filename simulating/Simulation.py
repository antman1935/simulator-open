class Reference:
    def __init__(self, value, minimum, maximum):
        self._value = value
        self.min = minimum
        self.max = maximum

    def get(self):
        return self._value
    
    def get_normalized(self):
        return  (self._value - self.min) / (self.max - self.min)
    
    def set(self, value):
        self._value = value

class SimObject:
    def __init__(self):
        raise Exception("Abstract base should not be initialized")
    
    """
    Based on the current state of the system at time t, compute the next state at time
    t + 1. This should NOT update any references.
    """
    def step(self):
        raise Exception("Unimplemented")
    
    """
    References should be updated for each object at the end of a step. Updating before
    this causes objects to have different views of the system at each step.
    """
    def updateReferences(self):
        raise Exception("Unimplemented")
    
    """
    All simulation objects should export a set of references that other objects can use in
    in their calcution for the next step.
    """
    def getReferences(self) -> list[tuple[str, Reference]]:
        raise Exception("Unimplemented")

class Simulator:
    def __init__(self):
        self.objects = {}
        self.references = {}

    def AddObject(self, object_name: str, object: SimObject):
        assert object_name not in self.objects, f"'{object_name}' has already been used for another object."
        self.objects[object_name] = object
        for ref_name, ref in object.getReferences():
            fullname = object_name + '.' + ref_name
            print(fullname)
            self.references[fullname] = ref

        return object

    def step(self):
        for _, object in self.objects.items():
            object.step()

        for _, object in self.objects.items():
            object.updateReferences()

    def ref(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name]
