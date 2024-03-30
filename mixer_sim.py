from simulating.industrial_object_lib.SimpleModeledMixer import MixerConfig, Mixer
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
        
    # Define all of the objects in situation
    sim = Simulator()
    config = MixerConfig(level_model_id, temp_model_id)
    mixer = sim.AddObject("Mixer", Mixer(config))

    # Run the simulation and generate new timeseries from model
    iters = 1000
    series = {"time": [], "temp": [], "level": [], "in1": [], "in2": [], "out": []}
    step = 0
    mixing_time = 30
    for iter in range(iters):
        match (step):
            case 0:
                if mixer.level < 600 and mixer.outlet.position == 0:
                    mixer.inlet1.cls_ref.set(True)
                    mixer.inlet1.ols_ref.set(True)
                elif mixer.level >= 600:
                    mixer.inlet1.cls_ref.set(False)
                    mixer.inlet1.ols_ref.set(False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 3:
                if mixer.level < 980 and mixer.inlet1.position == 0:
                    mixer.inlet2.cls_ref.set(True)
                    mixer.inlet2.ols_ref.set(True)
                elif mixer.level >= 980:
                    mixer.inlet2.cls_ref.set(False)
                    mixer.inlet2.ols_ref.set(False)
                    print(f"step {step} complete at iter {iter}")
                    step += 1
            case 18:
                if mixer.level > 0 and mixer.inlet2.position == 0:
                    mixer.outlet.cls_ref.set(True)
                    mixer.outlet.ols_ref.set(True)
                elif mixer.level == 0:
                    mixer.outlet.cls_ref.set(False)
                    mixer.outlet.ols_ref.set(False)
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
        series['in1'].append(mixer.inlet1.position)
        series['in2'].append(mixer.inlet2.position)
        series['out'].append(mixer.outlet.position)

    plt.plot(series['time'], series['level'])
    plt.plot(series['time'], series['temp'])
    plt.title(f"{temp_model_id}+{level_model_id}")
    plt.show()
