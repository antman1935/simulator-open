from modeling.NeuralCDE import NeuralCDEDefinition
from modeling.ForecastRNN import ForecastRNNDefinition
from modeling.TimeSeriesNNRunner import TimeSeriersNNRunner
from util.Exportable import Exportable, ExportableType

if __name__ == "__main__":
    model_id = None
    defn = None
    model = None
    optimizer = None

    # load the model if we've saved one to a file.
    if model_id is not None:
        defn = Exportable.loadExportable(ExportableType.Model, model_id)
    # otherwise define a model and train it
    else:
        defn = ForecastRNNDefinition(
            datasource="mixer simulation dataset.csv",
            input_features= ['Mixer100_Inlet1_Position',
                                'Mixer100_Inlet2_Position',
                                'Mixer100_Outlet_Position',
                                'Mixer100_Level_PV',
                                'Mixer100_Temperature_PV'],
            output_features= ['Mixer100_Temperature_PV'],
            frame_size=8,
            overlap=1,
            maximum_frames=0,
            epochs=4,
            train_batch_size=8,
            layers=[
                ("LSTM", 512, {"bidirectional": True}),
                ("LSTM", 256, {})
            ],
            convolution=True)
            # hidden_channels=128,
            # hidden_layer_widths=[128],
            # dropout_layers=[False, False],
            # interpolation="cubic")
        
    runner = TimeSeriersNNRunner(defn)

    if runner.trainedModelExists():
        model, optimizer = runner.load()
    else:
        model, optimizer = runner.train()
    
    runner.test(model)
    model_id = defn.exportableDescriptor()
    print("Model produced/tested:", model_id)