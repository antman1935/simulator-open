from simulating.SimObject import SimObject, Reference
import torch
import torchcde
import numpy as np

class ModeledObject(SimObject):
    def __init__(self, model: torch.nn.Module, datapoint_length: int, cubic: bool, input_references: list[Reference]):
        self.model = model
        self.datapoint_length = datapoint_length
        self.cubic = cubic
        self.input_references = input_references

        self.state_data = {"t": [i / float(datapoint_length) for i in range(datapoint_length)]}
        self.initial_state_set = False
        self.output = None
        
    def setInitialState(self, initial_series: list[list[float]]):
        assert len(initial_series) == len(self.input_references), f"Incorrect number of initial series for model {self.model_name}"
        for i, series in enumerate(initial_series):
            assert len(series) == self.datapoint_length, f"{i}th initial state series for model "\
                                               f"{self.model_name} is incorrect length"\
                                               f" (correct: {self.datapoint_length} vs actual: "\
                                               f"{len(series)})."
            self.state_data[f"input{i}"] = series

        # transpose the data while storing in 2d array
        self.state_data = [[self.state_data['t'][i]] + [self.state_data[f"input{j}"][i] for j in range(len(self.input_references))] for i in range(self.datapoint_length)]
        self.initial_state_set = True

    def step(self):
        assert self.initial_state_set

        # drop oldest frame
        self.state_data = self.state_data[1:]

        # shift time down
        t1 = self.state_data[0][0]
        for row in self.state_data:
            row[0] -= t1

        # insert newest frame
        self.state_data.append([float(self.datapoint_length - 1) / (self.datapoint_length)] + [ref.get_normalized() for ref in self.input_references])

        X = torch.from_numpy(np.array([self.state_data]))
        X = torch.tensor(X.clone().detach().requires_grad_(True), dtype=torch.float)
        if self.cubic:
            X = torchcde.hermite_cubic_coefficients_with_backward_differences(X)
        pred_y = self.model(X).squeeze(-1)

        self.output = pred_y

