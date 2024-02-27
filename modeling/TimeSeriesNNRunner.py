from modeling.TimeSeriesNNDefinition import TimeSeriesNNDefinition
from modeling.util.data_import import importData, getDataForTraining
from datetime import datetime
import json
import math
import torch
import torchcde
import os

def load_tsnn_definition(id):
    parameters = None
    with open(f"modeling/hyperparameters/{id}.json", "r") as openfile:
        # Reading from json file
        parameters = json.load(openfile)

    cls_str = parameters["__class__"]
    del parameters["__class__"]

    match (cls_str):
        case "<class 'modeling.NeuralCDE.NeuralCDEDefinition'>":
            from modeling.NeuralCDE import NeuralCDEDefinition
            return NeuralCDEDefinition(**parameters)
        case _:
            raise Exception("invalid definition class")

class TimeSeriersNNRunner:
    def __init__(self, defn: TimeSeriesNNDefinition):
        self.defn = defn
        self.dataset = None
        self.testset = None
        self.time_dimension = 'DateTime'

    def load(self):
        id = self.defn.moduleDescriptor()
        model_path = f"modeling/models/{id}.model"
        if not os.path.exists(model_path):
            raise Exception(f"Model specified by parameters {id} does not exist. Please train and save it.")
        
        checkpoint = torch.load(model_path)
        model = checkpoint['model']
        optimizer = checkpoint['optimizer']

        return model, optimizer
    
    def train(self):
        # read in the csv
        self.dataset, self.testset = importData(self.defn.datasource, self.defn.frame_size, self.defn.maximum_frames, self.defn.overlap)
        dataset_size = len(self.dataset)

        id = self.defn.moduleDescriptor()

        # save parameters for reference
        parameter_path = f"modeling/hyperparameters/{id}.json"
        params = json.dumps(self.defn.export(), sort_keys=False, indent=3)
        with open(parameter_path, "w+") as outfile:
            outfile.write(params)

        # preprocess it so that we can input it into our training/testing
        # X is of the shape [#time series, #data points in each, #features at each point]
        X, y = getDataForTraining(self.dataset, self.time_dimension, self.defn.input_features, self.defn.output_features)
        train_coeffs = torchcde.hermite_cubic_coefficients_with_backward_differences(X)
        # no longer needed, free the memory
        self.dataset = None
        X = None

        # train model on the data
        model = self.defn.generateModule()
        # TODO: made an enum for controlling this, leave as default for now
        optimizer = torch.optim.Adam(model.parameters())
        model.train()

        train_dataset = torch.utils.data.TensorDataset(train_coeffs, y)
        train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=self.defn.train_batch_size)
        batches = dataset_size // self.defn.train_batch_size
        for epoch in range(self.defn.epochs):
            batch_count = 0
            epoch_start = datetime.now()
            for batch in train_dataloader:
                batch_start = datetime.now()
                batch_coeffs, batch_y = batch
                pred_y = model(batch_coeffs)
                loss = torch.nn.functional.mse_loss(pred_y, batch_y)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                batch_end = datetime.now()
                print(f"Epoch {epoch}/ Batch {batch_count} of {batches}({int(100 * (batch_count / batches))}%): start: {batch_start} - end: {batch_end}    ", end='\r')
                batch_count += 1
            epoch_end = datetime.now()
            print(f"Epoch: {epoch}   Training loss: {loss.item()}   start: {epoch_start}    end: {epoch_end}")

        model_path = f"modeling/models/{id}.model"
        torch.save({"model": model, "optimizer": optimizer}, model_path)

        

        return model, optimizer
    
    def test(self, model):
        if self.testset is None:
            _, self.testset = importData(self.defn.datasource, self.defn.frame_size, self.defn.maximum_frames, self.defn.overlap)

        model.eval()
        test_X, test_y = getDataForTraining(self.testset, self.time_dimension, self.defn.input_features, self.defn.output_features)
        print("Testing dataset size", test_X.size())
        test_coeffs = torchcde.hermite_cubic_coefficients_with_backward_differences(test_X)
        pred_y = model(test_coeffs)

        prediction_miss = (pred_y - test_y)
        mags = []
        miss_mags = []
        for i, pred in enumerate(pred_y):
            mags.append(pred.norm())
        for i, miss in enumerate(prediction_miss):
            miss_mags.append(miss.norm())
        classes = {}
        for miss_mag, mag in zip(miss_mags, mags):
            cls = int(math.log(mag, 2))
            if not cls in classes:
                classes[cls] = {"ratio":[], "total": []}
            classes[cls]["ratio"].append(miss_mag/mag)
            classes[cls]["total"].append(miss_mag)

        for cls in sorted(classes.keys()):
            count = len(classes[cls]['ratio'])
            total_miss = sum(classes[cls]['total'])
            avg_miss = total_miss / count
            avg_miss_ratio = sum(classes[cls]['ratio']) / count
            print(f"class {cls} (2^{cls}):"\
                f"             count: {count}"\
                f"    total miss mag: {total_miss}"\
                f"      avg miss mag: {avg_miss}"\
                f"    avg miss ratio: {avg_miss_ratio}")
        average_miss_mag = sum([miss_mags[i]/ mags[i] for i in range(len(mags))]) / len(mags)
        print(f"avg_miss_ratio: {average_miss_mag}")
        print(f"miss norm:", prediction_miss.norm())