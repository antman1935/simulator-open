from simulating.SimObject import Reference
from simulating.ModeledObject import ModeledObject
import torch

class MixerLevelModel(ModeledObject):
    def __init__(self, model: torch.nn.Module, datapoint_length: int, cubic: bool, inlet1_position: Reference, inlet2_position: Reference, outlet_position: Reference):
        self.level = 0
        self.level_ref = Reference(0, 0, 1000)
        self.inlet1_position = inlet1_position
        self.inlet2_position = inlet2_position
        self.outlet_position = outlet_position
        super().__init__(model, datapoint_length, cubic, [inlet1_position, inlet2_position, outlet_position, self.level_ref])
        self.setInitialState([[0 for _ in range(datapoint_length)],
                              [0 for _ in range(datapoint_length)],
                              [0 for _ in range(datapoint_length)],
                              [0 for _ in range(datapoint_length)]])
        
    def step(self):
        super().step()
        if (self.inlet1_position.get() != 100 and self.inlet2_position.get() != 100 and self.outlet_position.get() != 100):
            pass # level stays the same if all valves are closed
        else:
            self.level = min(max(0, self.output[0].item()), 1) * 1000
            if self.level < 20:
                self.level = 0

    def updateReferences(self):
        self.level_ref.update(self.level)

    def getReferences(self) -> list[tuple[str, Reference]]:
        return [("Level", self.level_ref)]