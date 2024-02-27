from simulating.MixerSimulation import MixerConfig, Mixer, Valve
from simulating.Simulation import Simulator
from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner, load_tsnn_definition
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Define the models we want to load from a file
    temp_model_id = "1825835231"
    level_model_id = "1789266116"
    
    level_model_defn = load_tsnn_definition(level_model_id)
    temp_model_defn = load_tsnn_definition(temp_model_id)

    level_model, _ = TimeSeriersNNRunner(level_model_defn).load()
    temp_model, _ = TimeSeriersNNRunner(temp_model_defn).load()
        
    # Define all of the objects in situation
    sim = Simulator()
    inlet1 = sim.AddObject("Inlet1", Valve())
    inlet2 = sim.AddObject("Inlet2", Valve())
    outlet = sim.AddObject("Outlet", Valve())
    config = MixerConfig(level_model, temp_model, level_model_defn.frame_size, temp_model_defn.frame_size, sim.ref("Inlet1.Position"), sim.ref("Inlet2.Position"), sim.ref("Outlet.Position"))
    mixer = sim.AddObject("Mixer", Mixer(config))

    # Run the simulation and generate new timeseries from model
    iters = 1000
    series = {"time": [], "temp": [], "level": [], "in1": [], "in2": [], "out": []}
    step = 0
    mixing_time = 30
    for iter in range(iters):
        match (step):
            case 0:
                if mixer.level < 600 and outlet.position == 0:
                    inlet1.open()
                elif mixer.level >= 600:
                    inlet1.close()
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 30:
                if mixer.level < 980 and inlet1.position == 0:
                    inlet2.open()
                elif mixer.level >= 980:
                    inlet2.close()
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 45:
                if mixer.level > 0 and inlet2.position == 0:
                    outlet.open()
                elif mixer.level == 0:
                    outlet.close()
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 46:
                # rollover to start again
                step = 0
            case _:
                step += 1
    
        # turn on 
        sim.step()
        series['time'].append(iter)
        series['level'].append(mixer.level)
        series['temp'].append(mixer.temp)
        series['in1'].append(inlet1.position)
        series['in2'].append(inlet2.position)
        series['out'].append(outlet.position)

    plt.plot(series['time'], series['level'])
    plt.plot(series['time'], series['temp'])
    plt.title(f"{temp_model_id}+{level_model_id}")
    plt.show()
