from simulating.SimObject import Reference
from simulating.ModeledObject import ModeledObject
import torch
import random

class MixerTemperatureModel(ModeledObject):
    def __init__(self, model: torch.nn.Module, datapoint_length: int, cubic: bool, inlet1_position: Reference, inlet2_position: Reference, outlet_position: Reference, level: Reference):
        self.temp = 121
        self.temperature_ref = Reference(121.0, 120.0, 165.0)
        self.inlet1_position = inlet1_position
        self.inlet2_position = inlet2_position
        self.outlet_position = outlet_position
        self.level = level
        super().__init__(model, datapoint_length, cubic, [inlet1_position, inlet2_position, outlet_position, self.level, self.temperature_ref])
        self.setInitialState([[0 for _ in range(datapoint_length)],
                              [0 for _ in range(datapoint_length)],
                              [0 for _ in range(datapoint_length)],
                              [0 for _ in range(datapoint_length)],
                              [random.random() / 100 for _ in range(datapoint_length)]])

    def step(self):
        super().step()
        self.temp = min(max(0, self.output[0].item()) + (random.random() / 100), 1) * 45 + 120

    def updateReferences(self):
        self.temperature_ref.update(self.temp)

    def getReferences(self) -> list[tuple[str, Reference]]:
        return [("Temperature", self.temperature_ref)]