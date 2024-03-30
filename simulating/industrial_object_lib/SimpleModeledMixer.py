from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner
from simulating.industrial_object_lib.Valve import Valve
from simulating.SimObject import SimObject, Reference
from simulating.ModeledObject import ModeledObject
from util.Exportable import Exportable, ExportableType
import torch
import random
    
class MixerLevelModel(ModeledObject):
    def __init__(self, model: torch.nn.Module, frames: int, inlet1_position: Reference, inlet2_position: Reference, outlet_position: Reference):
        self.level = 0
        self.level_ref = Reference(0, 0, 1000)
        self.inlet1_position = inlet1_position
        self.inlet2_position = inlet2_position
        self.outlet_position = outlet_position
        super().__init__(model, frames, [inlet1_position, inlet2_position, outlet_position, self.level_ref])
        self.setInitialState([[0 for _ in range(frames)],
                              [0 for _ in range(frames)],
                              [0 for _ in range(frames)],
                              [0 for _ in range(frames)]])
        
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
    
class MixerTemperatureModel(ModeledObject):
    def __init__(self, model: torch.nn.Module, frames: int, inlet1_position: Reference, inlet2_position: Reference, outlet_position: Reference, level: Reference):
        self.temp = 121
        self.temperature_ref = Reference(121.0, 120.0, 165.0)
        self.inlet1_position = inlet1_position
        self.inlet2_position = inlet2_position
        self.outlet_position = outlet_position
        self.level = level
        super().__init__(model, frames, [inlet1_position, inlet2_position, outlet_position, self.level, self.temperature_ref])
        self.setInitialState([[0 for _ in range(frames)],
                              [0 for _ in range(frames)],
                              [0 for _ in range(frames)],
                              [0 for _ in range(frames)],
                              [random.random() / 100 for _ in range(frames)]])

    def step(self):
        super().step()
        self.temp = min(max(0, self.output[0].item()), 1) * 45 + 120

    def updateReferences(self):
        self.temperature_ref.update(self.temp)

    def getReferences(self) -> list[tuple[str, Reference]]:
        return [("Temperature", self.temperature_ref)]
    
class Mixer(SimObject):
    def __init__(self, level_model_id: str, temp_model_id: str):
        self.inlet1 = Valve()
        self.inlet2 = Valve()
        self.outlet = Valve()

        level_model_defn = Exportable.loadExportable(ExportableType.Model, level_model_id)
        temp_model_defn = Exportable.loadExportable(ExportableType.Model,temp_model_id)

        level_model, _ = TimeSeriersNNRunner(level_model_defn).load()
        temp_model, _ = TimeSeriersNNRunner(temp_model_defn).load()
        
        self._level_model = MixerLevelModel(level_model, level_model_defn.datapoint_length, self.inlet1.position_ref, self.inlet2.position_ref, self.outlet.position_ref)
        self._temp_model = MixerTemperatureModel(temp_model, temp_model_defn.datapoint_length, self.inlet1.position_ref, self.inlet2.position_ref, self.outlet.position_ref, self._level_model.level_ref)
        self.level = self._level_model.level
        self.temp = self._temp_model.temp
        

    def step(self):
        self.inlet1.step()
        self.inlet2.step()
        self.outlet.step()
        self._level_model.step()
        self._temp_model.step()
        self.level = self._level_model.level
        self.temp = self._temp_model.temp

    def updateReferences(self):
        self.inlet1.updateReferences()
        self.inlet2.updateReferences()
        self.outlet.updateReferences()
        self._level_model.updateReferences()
        self._temp_model.updateReferences()

    def getReferences(self) -> list[tuple[str, Reference]]:
        return self._level_model.getReferences() + \
                self._temp_model.getReferences() + \
                [(f"Inlet1.{ref_name}", ref) for ref_name, ref in self.inlet1.getReferences()] + \
                [(f"Inlet2.{ref_name}", ref) for ref_name, ref in self.inlet2.getReferences()] + \
                [(f"Outlet.{ref_name}", ref) for ref_name, ref in self.outlet.getReferences()]