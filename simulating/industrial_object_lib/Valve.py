from simulating.SimObject import SimObject, Reference

class Valve(SimObject):
    def __init__(self):
        self._cls = False
        self._ols = False
        self._open = False
        self.position = 0
        self.cls_ref = Reference(0, 0, 1, read_only=False)
        self.ols_ref = Reference(0, 0, 1, read_only=False)
        self.position_ref = Reference(0, 0, 100)

    def step(self):
        self._cls = self.cls_ref.get()
        self._ols = self.ols_ref.get()
        self._open = self._cls and self._ols
        
        if self._open:
            self.position = min(100, self.position + 20)
        else:
            self.position = max(0, self.position - 20)

    def updateReferences(self):
       self.position_ref.update(self.position)

    def getReferences(self) -> list[tuple[str, Reference]]:
        return [("Position", self.position_ref), ("OLS", self.ols_ref), ("CLS", self.cls_ref)]