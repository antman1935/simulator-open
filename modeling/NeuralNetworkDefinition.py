import torch
from util.Exportable import Exportable

"""
Abstract base class for neural network definition. All parameters to the constructor
of a subclass should have a string representation that can be saved in JSON and then
used to reconstruct the actual parameter, if it is does not have a literal data type.
Note: You must do the reconstruction in the constructor.

A definition should completely determine the neural network that is
    * produced during training
        * it's dataset
        * parameters/method of data engineering/cleaning
        * set of features to train on and to predict
        * training parameters (optimizer, epochs, batch size, etc.)
    * evaluated
        * how to create a feature vector from a new input

This will allow us to save models with a unique idenitifier, and save the parameters
used to generate it with the same idenitifier so that we know what exactly is the
difference between each model (no more relying on hope).
"""
class NeuralNetworkDefinition(Exportable):

    def __init__(self):
        raise Exception("Abstract base class.")

    """
    Entirely up to the user on how to define this function.
    """
    def generateModule(self) -> torch.nn.Module:
        raise Exception("Unimplemented")



        