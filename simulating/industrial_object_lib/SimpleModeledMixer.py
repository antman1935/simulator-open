from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner
from simulating.industrial_object_lib.Valve import Valve
from simulating.industrial_object_lib.MixerLevelModel import MixerLevelModel
from simulating.industrial_object_lib.MixerTemperatureModel import MixerTemperatureModel
from simulating.SimObject import SimObject, Reference
from simulating.definition.SimulationDefiniton import SimObjectDefn
from util.Exportable import Exportable, ExportableType
    
class Mixer(SimObject):
    def __init__(self, level_model_id: str, temp_model_id: str):
        self.inlet1 = Valve()
        self.inlet2 = Valve()
        self.outlet = Valve()

        level_model_defn = Exportable.loadExportable(ExportableType.Model, level_model_id)
        temp_model_defn = Exportable.loadExportable(ExportableType.Model,temp_model_id)

        level_model, _ = TimeSeriersNNRunner(level_model_defn).load()
        temp_model, _ = TimeSeriersNNRunner(temp_model_defn).load()

        # TODO: Make cubic interpolation of datapoints a base TimeSeriesNNDefn field.
        self._level_model = MixerLevelModel(level_model, level_model_defn.datapoint_length, False, self.inlet1.position_ref, self.inlet2.position_ref, self.outlet.position_ref)
        self._temp_model = MixerTemperatureModel(temp_model, temp_model_defn.datapoint_length, False, self.inlet1.position_ref, self.inlet2.position_ref, self.outlet.position_ref, self._level_model.level_ref)
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
    
class SimpleModeledMixerDefn(SimObjectDefn):
    def __init__(self, level_model_id, temp_model_id):
        super().__init__(ref_map={})
        self.level_model_id = level_model_id
        self.temp_model_id = temp_model_id

    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "level_model_id": self.level_model_id,
            "temp_model_id": self.temp_model_id,
          }
        )
        return running

    def createSimObject(self) -> SimObject:
        return Mixer(level_model_id=self.level_model_id, temp_model_id=self.temp_model_id)