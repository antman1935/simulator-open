from util.Exportable import Exportable, ExportableType
from simulating.SimObject import Reference, SimObject
from simulating.Simulation import Simulator

class ExternalReference:
    def __init__(self, name: str, desc: str, required: bool = True):
        self.name = name
        self.description = desc
        self.required = required

"""
Subclass this to define an object type that can be used in a simulation.
The class should define:
    * The parameters needed to instantiate the object
    * The external object references.
    * method to instantiate the object.
"""
class SimObjectDefn(Exportable):
    """
    ref_map is the mapping from external reference to the actual resolved reference.
    """
    def __init__(self, ref_map: dict[str, str]):
        self.ref_map = ref_map
        for ext_ref in self.getExternalReferences():
            if ext_ref.required:
                assert ext_ref.name in ref_map.keys(), f"{ext_ref.name} expected to be set, but is not"

    def getExportType(self) -> ExportableType:
        return ExportableType.Simulation
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "refs": self.ref_map,
          }
        )
        return running
    
    """
    Override to return a SimObject subclass to add to the simulation.
    """
    def createSimObject(self) -> SimObject:
        raise Exception("Unimplemented")
    
    """
    Override to return a static list of name external references.
    """
    def getExternalReferences(self) -> list[ExternalReference]:
        return []
    
    """
    After all objects in a given simulation definition are created in
    a simulation instance, each object defn has this method called with
    the object it created as the first parameter. 
    If an object is dependent on a reference exported from an external
    object, it must implement the resolveReferences method and save the
    references it wants to use.
    """
    def resolveReferences(self, object: SimObject, references: dict[str, Reference]):
        resolutions = {}
        for ext_ref_name, ref_name in self.ref_map.items():
            if not ref_name in references:
                # TODO: refactor to make it possible to check this at the time of saving the simulation
                raise Exception(f"Reference {ref_name} does not exist (ext_ref: {ext_ref_name})")
            resolutions[ext_ref_name] = references[ref_name]
        object.resolveReferences(resolutions)

"""
This class defines a simulation to run in our server and provides a method
to create a simulation instance from the definition.
The working of the simulation is defined by the inner working of each object
and which references they share between each other.
"""
class SimulationDefn(Exportable):
    def __init__(self, objects: dict[str, SimObjectDefn]):
        self.objects = objects

    def getExportType(self) -> ExportableType:
        return ExportableType.Simulation
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "objects": {obj_name: obj_defn.export() for obj_name, obj_defn in self.objects.items()},
          }
        )
        return running

    def createSimulation(self) -> Simulator:
        sim = Simulator()
        links = []
        for name, defn in self.objects.items():
            object = sim.AddObject(name, defn.createSimObject())
            links.append((defn, object))

        for (defn, object) in links:
            defn.resolveReferences(object, sim.references)

        return sim
    
    def load(sim_id: str):
        return Exportable.loadExportable(ExportableType.Simulation, sim_id)
    
