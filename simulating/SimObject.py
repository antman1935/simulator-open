class Reference:
    def __init__(self, value, minimum, maximum, read_only = True):
        self._value = value
        self.min = minimum
        self.max = maximum
        self.read_only = read_only

    def get(self):
        return self._value
    
    def get_normalized(self):
        return  (self.get() - self.min) / (self.max - self.min)
    
    def update(self, value):
        self._value = value

    def set(self, value):
         # TODO: error handling here that could be returned from the flask server
        assert not self.read_only, "Attempting to write to read only reference." # TODO: throw error so Server can report which reference it was
        self._value = value

class SimObject:
    def __init__(self):
        raise Exception("Abstract base should not be initialized")
    
    """
    Based on the current state of the system at time t, compute the next state at time
    t + 1. This should NOT update any references.
    """
    def step(self):
        self.step()
    
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
    
    """
    Override this method to connect named references defined in the object's definition.
    """
    def resolveReferences(self, refs: dict[str, Reference]):
        pass