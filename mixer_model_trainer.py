from modeling.NeuralCDE import NeuralCDEDefinition
from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner, load_tsnn_definition

if __name__ == "__main__":
    model_id = None #"1767966911"
    defn = None
    model = None
    optimizer = None

    # load the model if we've saved one to a file.
    if model_id is not None:
        defn = load_tsnn_definition(model_id)
    # otherwise define a model and train it
    else:
        defn = NeuralCDEDefinition(
            datasource="mixer simulation dataset.csv",
            input_features= ['Mixer100_Inlet1_Position',
                                'Mixer100_Inlet2_Position',
                                'Mixer100_Outlet_Position',
                                'Mixer100_Level_PV'],
            output_features= ['Mixer100_Temperature_PV'],
            frame_size=8,
            overlap=0.70,
            maximum_frames=5e4,
            epochs=4,
            train_batch_size=8,
            hidden_channels=128,
            hidden_layer_widths=[128, 64, 32, 64],
            dropout_layers=[False, False, False, True, False],
            interpolation="cubic")
        
    runner = TimeSeriersNNRunner(defn)

    if model_id is not None:
        model, optimizer = runner.load()
    else:
        model, optimizer = runner.train()
    
    runner.test(model)