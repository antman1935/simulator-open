import torch
from copy import copy
from zlib import adler32, crc32

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
class NeuralNetworkDefinition:

    def __init__(self):
        raise Exception("Abstract base class.")

    """
    Entirely up to the user on how to define this function.
    """
    def generateModule(self) -> torch.nn.Module:
        raise Exception("Unimplemented")
    
    """
    This function should export all of the parameters in the
    constructor of the NeuralNetworkDefinition subclass so
    that if the parameters are exported as
        params = definition.export()
        save_to_file(params, filename)
    a new definition could be instantiated from the file with
        params = load_from_file(filename)
        definition = NeuralNetworkDefinitionSubclass(**params)
    """
    def export(self) -> dict:
        # This is a special parameter that will be used to determine which class to load,
        # but will be deleted from the dictionary before instantiating the definition.
        return dict(copy({'__class__': str(type(self))}))
    
    """
    Unique ID generation happens here. It takes the hash of all
    the parameters in the export in a deterministic way.
    """
    def moduleDescriptor(self) -> str:
        params = self.export()
        _hash = adler32(bytes(params["__class__"], 'utf-8'))
        for key in sorted(params.keys()):
            if key == "__class__":
                continue
            _hash = adler32(bytes(str(_hash) + key + str(params[key]), 'utf-8'))

        return str(hex(_hash))[2:]



        