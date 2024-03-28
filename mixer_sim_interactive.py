from simulating.Simulation import SimulatorServer
import matplotlib.pyplot as plt
import time

def simulator_server():
    pass

if __name__ == "__main__":
    # simulator is created and runs in a backgroud process.
    simServer = SimulatorServer()
    series = {"time": [], "temp": [], "level": [], "in1": [], "in2": [], "out": []}
    plt.ion()
    
    # turn on 
    iters = 1000
    series = {"time": [], "temp": [], "level": [], "in1": [], "in2": [], "out": []}
    step = 0
    f = plt.figure()
    f_in = plt.figure()
    graph1 = f.add_subplot(211)
    graph2 = f.add_subplot(212)
    graph3 = f_in.add_subplot(111)
    # f.show()
    next_iter = 0
    loops = 0
    for iter in range(iters):
        time.sleep(0.9)
        match (step):
            case 0:
                if simServer.getReferenceValue("Mixer.Level") < 600 and simServer.getReferenceValue("Mixer.Outlet.Position") == 0:
                    simServer.setReferenceValue("Mixer.Inlet1.CLS", True)
                    simServer.setReferenceValue("Mixer.Inlet1.OLS", True)
                elif simServer.getReferenceValue("Mixer.Level") >= 600:
                    simServer.setReferenceValue("Mixer.Inlet1.CLS", False)
                    simServer.setReferenceValue("Mixer.Inlet1.OLS", False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 3:
                if simServer.getReferenceValue("Mixer.Level") < 980 and simServer.getReferenceValue("Mixer.Inlet1.Position") == 0:
                    simServer.setReferenceValue("Mixer.Inlet2.CLS", True)
                    simServer.setReferenceValue("Mixer.Inlet2.OLS", True)
                elif simServer.getReferenceValue("Mixer.Level") >= 980:
                    simServer.setReferenceValue("Mixer.Inlet2.CLS", False)
                    simServer.setReferenceValue("Mixer.Inlet2.OLS", False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 18:
                if simServer.getReferenceValue("Mixer.Level") > 0 and simServer.getReferenceValue("Mixer.Inlet2.Position") == 0:
                    simServer.setReferenceValue("Mixer.Outlet.CLS", True)
                    simServer.setReferenceValue("Mixer.Outlet.OLS", True)
                elif simServer.getReferenceValue("Mixer.Level") == 0:
                    simServer.setReferenceValue("Mixer.Outlet.CLS", False)
                    simServer.setReferenceValue("Mixer.Outlet.OLS", False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 19:
                # rollover to start again
                step = 0
                loops += 1
            case _:
                step += 1
    
        series['time'].append(iter)
        series['level'].append(simServer.getReferenceValue("Mixer.Level"))
        series['temp'].append(simServer.getReferenceValue("Mixer.Temperature"))
        series['in1'].append(simServer.getReferenceValue("Inlet1.Position"))
        series['in2'].append(simServer.getReferenceValue("Inlet2.Position"))
        series['out'].append(simServer.getReferenceValue("Outlet.Position"))

        graph1.clear()
        graph2.clear()
        graph3.clear()
        graph1.set_ylim(0, 1000)
        graph1.set_ylabel("Level")
        graph1.plot(series['time'][-(min(50, iters)):], series['level'][-(min(50, iters)):])
        graph2.set_ylim(110, 165)
        graph2.set_ylabel("Temperature")
        graph2.plot(series['time'][-(min(50, iters)):], series['temp'][-(min(50, iters)):])
        graph3.set_ylim(0, 100)
        graph3.set_ylabel("Position")
        graph3.plot(series['time'][-(min(50, iters)):], series['in1'][-(min(50, iters)):], label='in1')
        graph3.plot(series['time'][-(min(50, iters)):], series['in2'][-(min(50, iters)):], label='in2')
        graph3.plot(series['time'][-(min(50, iters)):], series['out'][-(min(50, iters)):], label='out')
        plt.pause(0.01)
        plt.show(block=False)

    simServer.stop()

