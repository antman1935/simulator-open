import os, sys

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    from simulating.definition.SimulationDefiniton import SimulationDefn
    from simulating.industrial_object_lib.SimpleModeledMixer import SimpleModeledMixerDefn
    from simulating.industrial_object_lib.ChainedModeledMixer import ChainedModeledMixerDefn

    sim_def = SimulationDefn(
        objects={
            "Mixer100": SimpleModeledMixerDefn(temp_model_id="9b6d688e-1a0ac5c1", level_model_id="9e4d503d-4a31070"),
            "Mixer200": SimpleModeledMixerDefn(temp_model_id="9b6d688e-1a0ac5c1", level_model_id="9e4d503d-4a31070"),
            "Mixer300": ChainedModeledMixerDefn(
                temp_model_id="9b6d688e-1a0ac5c1",
                level_model_id="9e4d503d-4a31070",
                ref_map={
                    'in1': 'Mixer100.Outlet.Position',
                    'in2': 'Mixer200.Outlet.Position',
                }),
        }
    )

    if not sim_def.fileAlreadyExists():
        sim_def.saveToFile(toJson=True)
        print(f"Saved simulation with id {sim_def.exportableDescriptor()}")
    else:
        print(f"Simulation with id {sim_def.exportableDescriptor()} already exists.")