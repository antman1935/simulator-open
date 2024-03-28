from multiprocessing import Pool, Lock, Process, Manager, Queue
from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner
from simulating.SimObject import SimObject, Reference
from simulating.MixerSimulation import Valve, Mixer, MixerConfig
from util.Exportable import Exportable, ExportableType
from time import sleep, time
from enum import Enum

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
            print(fullname)
            self.references[fullname] = ref

        return object

    def step(self):
        if not self.simulation_started:
            self.simulation_started = True

        for object in self.objects.values():
            object.step()

        for _, object in self.objects.items():
            object.updateReferences()

    def getReferences(self):
        return self.references.keys()
    
    def setReferenceValue(self, ref_name, value):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        self.references[ref_name].set(value)

    def getReferenceValue(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name].get()
    
    def ref(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name]
    
class Operation(Enum):
    READ = 1
    WRITE = 2
    
def simulation_runner(simulation_defn, inQueue, outQueue):
    # TODO: define a simulation definition class to generate a simulation from
    # a static definition here.
    # load simulation file and instantiate all objects in a simulator env
    temp_model_id = "c96605d-69845ace"
    level_model_id = "b478c98b-f98110f3"
    
    level_model_defn = Exportable.loadExportable(ExportableType.Model, level_model_id)
    temp_model_defn = Exportable.loadExportable(ExportableType.Model,temp_model_id)

    level_model, _ = TimeSeriersNNRunner(level_model_defn).load()
    temp_model, _ = TimeSeriersNNRunner(temp_model_defn).load()
        
    # Define all of the objects in situation
    sim = Simulator()
    inlet1 = sim.AddObject("Inlet1", Valve())
    inlet2 = sim.AddObject("Inlet2", Valve())
    outlet = sim.AddObject("Outlet", Valve())
    config = MixerConfig(level_model, temp_model, level_model_defn.datapoint_length, temp_model_defn.datapoint_length, sim.ref("Inlet1.Position"), sim.ref("Inlet2.Position"), sim.ref("Outlet.Position"))
    mixer = sim.AddObject("Mixer", Mixer(config))

    runtime = 0
    while True:
        start = time()
        # print(start)
        sim.step()
        end = time()
        # print(f"step took {end-start} seconds")
        runtime = end - start
        next_work_time = end + (1.0 - runtime)
        while (time() < next_work_time):
            if (inQueue.empty()):
                sleep(0.01)
            else:
                query, args = inQueue.get()

                match (query):
                    case Operation.READ:
                        id, reference = args
                        value = sim.getReferenceValue(reference)
                        outQueue.put((id, value))
                    case Operation.WRITE:
                        id, reference, value = args
                        sim.setReferenceValue(reference, value)
                        outQueue.put((id, True))
    pass
    
class SimulatorServer:
    def __init__(self, simulation_defn = "PO-TAY-TOES"):
        self.inQueue = Queue()
        self.outQueue = Queue()
        self.sim_process = Process(target=simulation_runner, args = (simulation_defn, self.inQueue, self.outQueue))
        self.sim_process.start()
        self.lock = Lock() # only used to get request id
        self.req_id = 0
        self.next_req = 0
        
    def setReferenceValue(self, ref_name, value):
        id = None
        with self.lock:
            id = self.req_id
            self.req_id += 1
        self.inQueue.put((Operation.WRITE, (id, ref_name, value)))

        while self.next_req != id:
            sleep(0.05)

        val, ret = self.outQueue.get()
        self.next_req += 1
        assert val == id and ret, "Set query failed."
        return ret

    def getReferenceValue(self, ref_name):
        id = None
        with self.lock:
            id = self.req_id
            self.req_id += 1
        self.inQueue.put((Operation.READ, (id, ref_name)))

        while self.next_req != id:
            sleep(0.05)

        val, ret = self.outQueue.get()
        self.next_req += 1
        assert val == id, "Set query failed."
        return ret
    
    def stop(self):
        self.sim_process.kill()
