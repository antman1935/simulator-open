from multiprocessing import Process, Queue
import asyncio
from simulating.SimObject import SimObject
from simulating.industrial_object_lib.SimpleModeledMixer import Mixer, MixerConfig
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
    
    def setReferences(self, mapping):
        for key, value in mapping.items():
            self.setReferenceValue(key, value)

    def getReferences(self, names):
        ret = {}
        for name in names:
            ret[name] = self.getReferenceValue(name)
        return ret
    
    def ref(self, ref_name):
        assert ref_name in self.references, f"'{ref_name}' does not exist."
        return self.references[ref_name]
    
class Operation(Enum):
    STOP = 0
    GET = 1
    SET = 2
    MULTIGET = 3
    MULTISET = 4
    
def simulation_runner(simulation_defn, inQueue, outQueue):
    # TODO: define a simulation definition class to generate a simulation from
    # a static definition here.
    # load simulation file and instantiate all objects in a simulator env
    temp_model_id = "9b6d688e-1a0ac5c1"
    level_model_id = "9e4d503d-4a31070"
        
    # Define all of the objects in situation
    sim = Simulator()
    config = MixerConfig(level_model_id, temp_model_id)
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
                id, operation, args = inQueue.get()

                match (operation):
                    case Operation.GET:
                        reference = args
                        value = sim.getReferenceValue(reference)
                        outQueue.put((id, value))
                    case Operation.MULTIGET:
                        names = args
                        value = sim.getReferences(names)
                        outQueue.put((id, value))
                    case Operation.SET:
                        reference, value = args
                        sim.setReferenceValue(reference, value)
                        outQueue.put((id, True))
                    case Operation.MULTISET:
                        mapping = args
                        sim.setReferences(mapping)
                        outQueue.put((id, True))
                    case Operation.STOP:
                        while not inQueue.empty():
                            id, operation, args = inQueue.get()
                            outQueue.put((id, "Server shutting down."))
                        return
    
class SimulatorServer:
    def __init__(self, simulation_defn = "PO-TAY-TOES"):
        self.inQueue = Queue()
        self.outQueue = Queue()
        self.sim_process = Process(target=simulation_runner, args = (simulation_defn, self.inQueue, self.outQueue))
        self.sim_process.start()
        self.req_id = 0
        self.next_req = 0
        self.out_flag = asyncio.Event()
        self.stopping = False

    async def _processRequest(self, operation: Operation, parameters):
        if self.stopping:
            return "Server shutting down."
        
        # get req id
        id = self.req_id
        self.req_id += 1

        self.out_flag.clear()
        self.inQueue.put((id, operation, parameters))

        # wait until we know the next_req has changed to our turn
        while self.next_req != id:
            await self.out_flag.wait()
        self.out_flag.clear()

        # TODO: this blocks until the queue has a value. Ideally we could 
        # have a flag that is set only when the outQueue has data. We'd
        # end up with a liveness coroutine that checks the queue, sets the
        # flag if there is data, and sleeps for some small epsilon. I
        # don't like the sound of it, so I am leaving this blocking wait
        # until I decide what to do.
        val, ret = self.outQueue.get()
        assert val == id, f"Response id {val} does not match expectations {id}."

        # notify waiters that it is their turn
        self.next_req += 1
        self.out_flag.set()
        return ret
        
    async def setReferenceValue(self, ref_name, value):
        return self._processRequest(Operation.SET, (ref_name, value))

    async def getReferenceValue(self, ref_name):
        return await self._processRequest(Operation.GET, ref_name)
    
    async def setReferences(self, mapping):
        return await self._processRequest(Operation.MULTISET, mapping)

    async def getReferences(self, names):
        return await self._processRequest(Operation.MULTIGET, names)
    
    def stop(self):
        self.stopping = True
        self.inQueue.put((-1, Operation.STOP, None))
        self.sim_process.join()
