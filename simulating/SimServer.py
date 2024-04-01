from multiprocessing import Process, Queue
import asyncio
from simulating.definition.SimulationDefiniton import SimulationDefn
from simulating.Simulation import SimulationError
from time import sleep, time
from enum import Enum

class Operation(Enum):
    STOP = 0
    GET_API = 1
    GET = 2
    SET = 3
    MULTIGET = 4
    MULTISET = 5
    
def simulation_runner(sim_id: str, inQueue, outQueue):
    defn = SimulationDefn.load(sim_id)
        
    sim = defn.createSimulation()

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
                    case Operation.STOP:
                        while not inQueue.empty():
                            id, operation, args = inQueue.get()
                            outQueue.put((id, "Server shutting down."))
                        return
                    case Operation.GET_API:
                        api = sim.getAPI()
                        outQueue.put((id, api))
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
                        e = sim.setReferenceValue(reference, value)
                        outQueue.put((id, e))
                    case Operation.MULTISET:
                        mapping = args
                        e = sim.setReferences(mapping)
                        outQueue.put((id, e))
                    
    
class SimulatorServer:
    def __init__(self, sim_id: str):
        self.inQueue = Queue()
        self.outQueue = Queue()
        self.sim_process = Process(target=simulation_runner, args = (sim_id, self.inQueue, self.outQueue))
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
        if isinstance(ret, SimulationError):
            raise Exception(str(ret.error_type), ret.msg)
        return ret
    
    async def getAPI(self):
        return await self._processRequest(Operation.GET_API, None)
        
    async def setReferenceValue(self, ref_name, value):
        return await self._processRequest(Operation.SET, (ref_name, value))

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