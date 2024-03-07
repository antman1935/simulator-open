from simulating.MixerSimulation import MixerConfig, Mixer, Valve
from simulating.Simulation import Simulator
from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner
from util.Exportable import Exportable, ExportableType
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Define the models we want to load from a file
    # 256-RRN level, 256-RNN w/ Conv temp
    # temp_model_id = "dc593797-fd6b0d30"
    # level_model_id = "b478c98b-f98110f3"

    # 256-RRN level, 512-RNN w/ Conv temp
    # temp_model_id = "9f5b9773-8313d5cf"
    # level_model_id = "b478c98b-f98110f3"

    # 256-RNN level, 128x128RNN w/ Conv
    # temp_model_id = "1307207-453533fd"
    # level_model_id = "b478c98b-f98110f3"

    # 256-RNN level, 128(bi)x128RNN w/ Conv
    # temp_model_id = "ffb4c6ef-5ea62e0f"
    # level_model_id = "b478c98b-f98110f3"

    # 256-RNN level, 256(bi)x256RNN w/ Conv
    temp_model_id = "c96605d-69845ace"
    level_model_id = "b478c98b-f98110f3"
    
    
    
    level_model_defn = Exportable.loadExportable(ExportableType.Model, level_model_id)
    temp_model_defn = Exportable.loadExportable(ExportableType.Model, temp_model_id)

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
                    inlet1.cls_ref.set(True)
                    inlet1.ols_ref.set(True)
                elif mixer.level >= 600:
                    inlet1.cls_ref.set(False)
                    inlet1.ols_ref.set(False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 3:
                if mixer.level < 980 and inlet1.position == 0:
                    inlet2.cls_ref.set(True)
                    inlet2.ols_ref.set(True)
                elif mixer.level >= 980:
                    inlet2.cls_ref.set(False)
                    inlet2.ols_ref.set(False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 18:
                if mixer.level > 0 and inlet2.position == 0:
                    outlet.cls_ref.set(True)
                    outlet.ols_ref.set(True)
                elif mixer.level == 0:
                    outlet.cls_ref.set(False)
                    outlet.ols_ref.set(False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 19:
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
