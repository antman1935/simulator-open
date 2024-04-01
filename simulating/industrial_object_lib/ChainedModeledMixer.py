from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner
from simulating.industrial_object_lib.Valve import Valve
from simulating.industrial_object_lib.MixerLevelModel import MixerLevelModel
from simulating.industrial_object_lib.MixerTemperatureModel import MixerTemperatureModel
from simulating.SimObject import SimObject, Reference
from simulating.definition.SimulationDefiniton import ExternalReference, SimObjectDefn
from util.Exportable import Exportable, ExportableType
    
class DownstreamMixer(SimObject):
    def __init__(self, level_model_id: str, temp_model_id: str):
        self.inlet1_position = None
        self.inlet2_position = None
        self.outlet = Valve()

        # references to export
        self.temperature_ref = Reference(0, 0, 0)
        self.level_ref = Reference(0, 0, 0)

        self.level_model_defn = Exportable.loadExportable(ExportableType.Model, level_model_id)
        self.temp_model_defn = Exportable.loadExportable(ExportableType.Model,temp_model_id)

        self.level_model, _ = TimeSeriersNNRunner(self.level_model_defn).load()
        self.temp_model, _ = TimeSeriersNNRunner(self.temp_model_defn).load()
        

    def step(self):
        self.outlet.step()
        self._level_model.step()
        self._temp_model.step()
        self.level = self._level_model.level
        self.temp = self._temp_model.temp

    def updateReferences(self):
        self.outlet.updateReferences()
        self._level_model.updateReferences()
        self._temp_model.updateReferences()

    def getReferences(self) -> list[tuple[str, Reference]]:
        return [
            ("Level", self.level_ref),
            ("Temperature", self.temperature_ref),
            ("Inlet1.Position", self.inlet1_position), 
            ("Inlet2.Position", self.inlet2_position),
        ] + \
        [(f"Outlet.{ref_name}", ref) for ref_name, ref in self.outlet.getReferences()]
    
    def resolveReferences(self, refs: dict[str, Reference]):
        # TODO: Make cubic interpolation of datapoints a base TimeSeriesNNDefn field.
        self.inlet1_position = refs['in1']
        self.inlet2_position = refs['in2']
        self._level_model = MixerLevelModel(self.level_model, self.level_model_defn.datapoint_length, False, self.inlet1_position, self.inlet2_position, self.outlet.position_ref, level_out_ref=self.level_ref)
        self._temp_model = MixerTemperatureModel(self.temp_model, self.temp_model_defn.datapoint_length, False, self.inlet1_position, self.inlet2_position, self.outlet.position_ref, self.level_ref, temp_out_ref=self.temperature_ref)
        self.level = self._level_model.level
        self.temp = self._temp_model.temp
    
class ChainedModeledMixerDefn(SimObjectDefn):
    def __init__(self, level_model_id, temp_model_id, ref_map):
        super().__init__(ref_map=ref_map)
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
        return DownstreamMixer(level_model_id=self.level_model_id, temp_model_id=self.temp_model_id)
    
    def getExternalReferences(self) -> list[ExternalReference]:
        return [
            ExternalReference('in1', "Inlet1's position"),
            ExternalReference('in2', "Inlet2's position")
        ]