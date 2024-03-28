from modeling.data_eng.DataSource.DataSource import DataSource
from modeling.data_eng.DataSet.DataSet import DataSet
import pandas as pd
import torch
import torchcde

"""
This class takes a DataSource and transforms it into a form usable for training
neural network models.
"""
class PyTorchDataSet(DataSet):
    def __init__(self, source: DataSource, datapoint_length: int, input_features: list[str], output_features: list[str], overlap: float = 0.25, max_dataset_size: int = 0, cubic_interp: bool = False):
        super().__init__(source)
        self.datapoint_length = datapoint_length
        self.input_features = input_features
        self.output_features = output_features
        self.overlap = overlap
        self.max_dataset_size = max_dataset_size
        self.cubic_interp = cubic_interp
    
    """
    Format the data so that it can be fed into a training algorithm. 
    Override this method to apply a transformation. This method determines
    the return type of the get() method.
    """
    def formatData(self, frames: list[pd.DataFrame]):
        import util.progress as progress
        
        X = []
        y = []
        print("Converting dataframes to timeseries datapoints.")
        for i in range(len(frames)):
            frames[i].dropna(inplace=True)

            copy_size = int(self.overlap * self.datapoint_length)
            copy_size = max(copy_size, self.datapoint_length - 1)
            # label every sequence of X coordinates with the y coordinate one step in the future. 
            # Throw out the last x value because it has no label.
            for j in range(self.datapoint_length-1, frames[i].index.size-1):
                y_df = frames[i].at_time(frames[i].index[j+1])[self.output_features]
                x_df = frames[i][frames[i].index[j-self.datapoint_length + 1]:frames[i].index[j]][self.input_features]
                X.append(torch.concat((torch.tensor([[i / float(self.datapoint_length)] for i in range(self.datapoint_length)]), torch.tensor(x_df.values)), 1).float())
                y.append(torch.tensor(y_df.values).transpose(0, 1).squeeze(-1).float())

                if self.overlap > 0:
                    j -= (copy_size - 1)

            progress.bar(i, len(frames) - 1)


        X = torch.stack(X)
        y = torch.stack(y)
        if self.cubic_interp:
            X = torchcde.hermite_cubic_coefficients_with_backward_differences(X)

        throw_away = 0
        if self.max_dataset_size > 0:
            throw_away = (X.size(0) - self.max_dataset_size)/ X.size(0)

        if throw_away == 0:
            split = [0.8, 0.2]
            print("Ratio (train/test)", split)
            [train, test] =  torch.utils.data.random_split(torch.utils.data.TensorDataset(X, y), split)
        else:
            split = [(1.0-throw_away) * 0.8, (1.0-throw_away) * 0.2, throw_away]
            print("Ratio (train/test/throwout)", split)
            [train, test, _] =  torch.utils.data.random_split(torch.utils.data.TensorDataset(X, y), split)

        return train, test

    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "datapoint_length": self.datapoint_length,
            "input_features": self.input_features, 
            "output_features": self.output_features, 
            "overlap": self.overlap, 
            "max_dataset_size": self.max_dataset_size,
            "cubic_interp": self.cubic_interp,
          }
        )
        return running