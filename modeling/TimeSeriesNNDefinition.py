from modeling.NeuralNetworkDefinition import NeuralNetworkDefinition
from modeling.data_eng.DataSet.DataSet import DataSet
from util.Exportable import ExportableType

"""
TODO: This is out of date, but still a good explanation of how things are 
working. Main issue with it is it is data preparation parameters have been
moved out of the NN definition entirely. Instead, they are now inside
a DataSet class and that determines how data cleaning and prep is done.
We still include some parameters that define the dataset for convenience.

This is the primary class of neural networks that this repository is
concerned with, time series forcasters. The unifying theme of these
networks is that they train/predict on a sequence of points and the
label/prediction is the next value in the timeseries.

The majority of the commonality these models will have is in how the
data is prepared and cleaned.
    * We will be ingesting a single timeseries with n named dimensions.
    * Denote that timeseries as [d_0, d_2, ..., d_L] where L is the length
      and each d_i has a time and n dimensions associated with it
    * Specify a set of input features to define X = [x_0, x_1, ..., x_L]
      with each x_i being d_i with only the input features selected.
    * Likewise, specify a set of output features that defines a timeseries Y.
    * Our training set is then X' = [x_0, x_1, ..., x_{L-1}] and
      Y' = [y_1, y_2, ..., y_L] and we reindex, so thay pred(x'_i) = y'_i.
    * We have a dataset where the input features at the last time step are
      labeled with the output features at the next timestep.
    * We generate our dataset by selecting a frame size f, which defines
      the length of each 'datapoint' (i.e. the length of the subsequence).
      If we say f = 1, then we are working on a single point in time and
      out data set remains the same.
    * Otherwise, we generate a new dataset from X' and Y', call them X'_f
      and Y'_f respectively. A single element of X'_f will be a contiguous
      subsequence of f points in X', so it has the form
        [x'_i, x'_{i+1}, ..., x'_{i+f-1}]
      and it has the label y'_{i+f-1}, i.e. the label of the last point
      in the subsequence.
    * Finally, we give a concept of allowing overlap when generating our
      frames. Overlap is a float from 0 to 1 that determines how much of
      the previous frame should be copied into the new frame.
    * If overlap = 0, then each frame is contiguous and there are L/f frames.
    * If overlap > 0, then we have max(f-1, overlap * f) points coming
      from the previous frame, like so
        frame i:  [x'_j, x'_{j+1}, ..., x'_{j+f-1}]
      frame i+1:        [x'_k, x'_{k+1}, ..., x'_{k+f-1}]
      where j < k <= j+f.
"""
class TimeSeriesNNDefinition(NeuralNetworkDefinition):
    def __init__(self, 
                 dataset: DataSet, 
                 input_features: list[str], 
                 output_features: list[str], 
                 datapoint_length: int,
                 epochs = 2, 
                 train_batch_size:int = 8):
        self.dataset = dataset
        self.input_features = input_features
        self.output_features = output_features
        self.datapoint_length = datapoint_length
        self.epochs = epochs
        self.train_batch_size = train_batch_size
    
    def getExportType(self) -> ExportableType:
        return ExportableType.Model

    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "dataset": self.dataset.exportableDescriptor(),
            "input_features": self.input_features,
            "output_features": self.output_features,
            "datapoint_length": self.datapoint_length,
            "epochs": self.epochs,
            "train_batch_size": self.train_batch_size
          }
        )
        return running
