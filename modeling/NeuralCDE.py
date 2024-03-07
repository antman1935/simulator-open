import torch
from torch.nn.modules import Module
import torchcde
from modeling.TimeSeriesNNDefinition import TimeSeriesNNDefinition
import math


######################
# A CDE model looks like
#
# z_t = z_0 + \int_0^t f_\theta(z_s) dX_s
#
# Where X is your data and f_\theta is a neural network. So the first thing we need to do is define such an f_\theta.
# That's what this CDEFunc class does.
# Here we've built a small single-hidden-layer neural network, whose hidden layer is of width 128.
######################
class CDEFunc(torch.nn.Module):
    def __init__(self, input_channels: int, hidden_channels:int, hidden_layer_widths: list[int], dropout_layers: list[float]):
        ######################
        # input_channels is the number of input channels in the data X. (Determined by the data.)
        # hidden_channels is the number of channels for z_t. (Determined by you!)
        ######################
        super(CDEFunc, self).__init__()
        self.input_channels = input_channels
        self.hidden_channels = hidden_channels

        # the first hidden layer is passed in directly so that it is accessible in the
        # NCDE class.
        modules = []
        last_layer_width = hidden_channels
        for width, dropout in zip(hidden_layer_widths, dropout_layers[:-1]): # in range(len(hidden_layer_widths) - 1):
            # add dropout layer if the drop percentage is greater than 0
            if dropout > 0:
                modules.append(torch.nn.Dropout(dropout))

            # add hidden layer of the specified width for this depth
            modules.append(torch.nn.Linear(last_layer_width, width))
            last_layer_width = width

            # add ReLU nonlinearity for each hidden layer
            modules.append(torch.nn.ReLU())

        # the final output layer should be a linear map of size input_channels * hidden_channels
        modules.append(torch.nn.Linear(last_layer_width, input_channels * hidden_channels))
        modules.append(torch.nn.Tanh())
        # add dropout layer if the drop percentage is greater than 0
        if dropout_layers[-1] > 0:
            modules.append(torch.nn.Dropout(dropout_layers[-1]))

        self.function = torch.nn.Sequential(*modules)

    ######################
    # For most purposes the t argument can probably be ignored; unless you want your CDE to behave differently at
    # different times, which would be unusual. But it's there if you need it!
    ######################
    def forward(self, t, z):
        # z has shape (batch, hidden_channels)
        z = self.function(z)
        ######################
        # Ignoring the batch dimension, the shape of the output tensor must be a matrix,
        # because we need it to represent a linear map from R^input_channels to R^hidden_channels.
        ######################
        z = z.view(z.size(0), self.hidden_channels, self.input_channels)

        return z


######################
# Next, we need to package CDEFunc up into a model that computes the integral.
######################
class NeuralCDE(torch.nn.Module):
    def __init__(self, input_channels, hidden_channels, output_channels, hidden_layer_widths: list[int], dropout_layers: list[float], interpolation):
        super(NeuralCDE, self).__init__()

        self.initial = torch.nn.Linear(input_channels, hidden_channels)
        self.func = CDEFunc(input_channels, hidden_channels, hidden_layer_widths, dropout_layers)
        self.readout = torch.nn.Linear(hidden_channels, output_channels)
        self.interpolation = interpolation

    def forward(self, coeffs):
        if self.interpolation == 'cubic':
            X = torchcde.CubicSpline(coeffs)
        elif self.interpolation == 'linear':
            X = torchcde.LinearInterpolation(coeffs)
        else:
            raise ValueError("Only 'linear' and 'cubic' interpolation methods are implemented.")

        adjoint_params = tuple(self.func.parameters()) + (coeffs,)
        ######################
        # Easy to forget gotcha: Initial hidden state should be a function of the first observation.
        ######################
        X0 = X.evaluate(X.interval[0])
        z0 = self.initial(X0)

        ######################
        # Actually solve the CDE.
        ######################
        z_T = torchcde.cdeint(X=X,
                              z0=z0,
                              func=self.func,
                              t=X.interval,
                              adjoint_params=adjoint_params)

        ######################
        # Both the initial value and the terminal value are returned from cdeint; extract just the terminal value,
        # and then apply a linear map.
        ######################
        z_T = z_T[:, 1]
        pred_y = self.readout(z_T)
        return pred_y
    
class NeuralCDEDefinition(TimeSeriesNNDefinition):
    def __init__(self,
                 datasource: str, 
                 input_features: list[str], 
                 output_features: list[str], 
                 frame_size: int, 
                 overlap: float = 0.99, 
                 maximum_frames: int = 0, 
                 epochs=2, 
                 train_batch_size: int = 8, 
                 hidden_channels: int = 128, 
                 hidden_layer_widths: list[int] = [128], 
                 dropout_layers: list[float] = [True, True], 
                 interpolation="cubic"):
        super().__init__(datasource, input_features, output_features, frame_size, overlap, maximum_frames, epochs, train_batch_size)
        self.input_channels = len(input_features) + 1
        self.hidden_channels = hidden_channels
        self.output_channels = len(output_features)

        self.hidden_layer_widths = hidden_layer_widths
        self.dropout_layers = dropout_layers

        assert len(hidden_layer_widths) > 0, "CDEFunc requires that we have at least one hidden layer"
        assert len(hidden_layer_widths) + 1  == len(dropout_layers), "There should be a dropout layer setting for the input to each layer."

        self.interpolation = interpolation

    

    def generateModule(self) -> Module:
        return NeuralCDE(self.input_channels,
                         self.hidden_channels,
                         self.output_channels,
                         self.hidden_layer_widths,
                         self.dropout_layers,
                         self.interpolation)
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "hidden_channels": self.hidden_channels,
            "hidden_layer_widths": self.hidden_layer_widths,
            "dropout_layers": self.dropout_layers,
            "interpolation": self.interpolation
          }
        )
        return running


