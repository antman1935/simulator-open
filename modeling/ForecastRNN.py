from typing import Iterator
import torch
from torch.nn.modules import Module
from torch.nn.parameter import Parameter
import torchcde
from modeling.TimeSeriesNNDefinition import TimeSeriesNNDefinition, DataSet

class ForecastRNN(torch.nn.Module):
    def __init__(self, datapoint_length: int, input_channels: int, layers: list[tuple[str, int, dict]], output_channels: int, convolution: bool):
        super(ForecastRNN, self).__init__()
        self.datapoint_length = datapoint_length
        self.input_channels = input_channels
        self.output_channels = output_channels
        self.convolution = convolution

        if convolution:
            conv_features = input_channels * input_channels   
            self.conv = torch.nn.Conv1d(input_channels, conv_features, self.datapoint_length // 2, groups=input_channels)
            prev_layer_channels = conv_features
        else:
            self.conv = None
            prev_layer_channels = self.input_channels

        self.rnns = []
        for model_type, hidden_channels, kwargs in layers:
            if model_type == "LSTM":
                self.rnns.append(torch.nn.LSTM(prev_layer_channels, hidden_channels, batch_first=True, **kwargs))
            elif model_type == "RNN":
                self.rnns.append(torch.nn.RNN(prev_layer_channels, hidden_channels, batch_first=True, **kwargs))
            elif model_type == "GRU":
                self.rnns.append(torch.nn.GRU(prev_layer_channels, hidden_channels, batch_first=True, **kwargs))
            else:
                raise Exception("Invalid RNN selected:", model_type)
            prev_layer_channels = hidden_channels
            if 'bidirectional' in kwargs and kwargs['bidirectional']:
                prev_layer_channels *= 2

        self.fcs = [torch.nn.Linear(prev_layer_channels, 1) for _ in range(output_channels)]

    def forward(self, X):
        # X has shape (batch, length, hidden_channels)
        if not self.conv is None:
            inp = self.conv(X.transpose(1,2)).transpose(1,2)
        else:
            inp = X
            
        for rnn in self.rnns:
            inp, hidden = rnn(inp)
        
        # last output from the rnn is the predicted value
        out = inp[:,-1,:]

        out = torch.concat([fc(out) for fc in self.fcs], 1)

        return out
    
    def parameters(self, recurse: bool = True) -> Iterator[Parameter]:
        params = []
        if not self.conv is None:
            params += self.conv.parameters()

        for layer in self.rnns:
            params += layer.parameters()

        for fc in self.fcs:
            params += fc.parameters()

        return params
    
class ForecastRNNDefinition(TimeSeriesNNDefinition):
    def __init__(self,
                 dataset: DataSet, 
                 input_features: list[str], 
                 output_features: list[str], 
                 datapoint_length: int, 
                 epochs=2, 
                 train_batch_size: int = 8, 
                 layers: list[tuple[str, int, dict]] = [("LSTM", 128, {})],
                 convolution: bool = False):
        super().__init__(dataset, input_features, output_features, datapoint_length, epochs, train_batch_size)
        self.input_channels = (len(input_features) + 1)
        self.layers = layers
        self.output_channels = len(output_features)
        self.convolution = convolution
    

    def generateModule(self) -> Module:
        return ForecastRNN(self.datapoint_length,
                         self.input_channels,
                         self.layers,
                         self.output_channels,
                         self.convolution)
    
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "layers": [[val for val in layer] for layer in self.layers],
            "convolution": self.convolution
          }
        )
        return running