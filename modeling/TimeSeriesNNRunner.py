from modeling.TimeSeriesNNDefinition import TimeSeriesNNDefinition
from datetime import datetime
import json
import math
import torch
import torchcde
import os
        
class CustomLoss(torch.nn.Module):
    # min determines how close to 0 we can get in determining % wise error
    # set too high -> loss from small values is minimized -> typically don't go to zero
    # set too low -> loss from small values is 
    def __init__(self, min: float = 0.0018):
        super().__init__()
        self.min = min
        self.ones = None

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor):
        if self.ones is None:
            self.ones = torch.ones_like(inputs)
        # return torch.minimum(torch.nn.functional.l1_loss((inputs + self.ones).log(), (targets + self.ones).log()), torch.tensor(self.max))
        # return torch.sum(self.ones - (torch.abs(targets - inputs ).log()))
        sign = targets.sign()
        sign[sign == 0] = 1
        clamped = targets.abs().clamp(self.min)
        clamped = sign * clamped
        
        return torch.sum((torch.abs(inputs - clamped) / torch.abs(clamped))**2)

class TimeSeriersNNRunner:
    def __init__(self, defn: TimeSeriesNNDefinition):
        self.defn = defn
        self.dataset = None
        self.testset = None
        self.time_dimension = 'DateTime'

    def trainedModelExists(self):
        id = self.defn.exportableDescriptor()
        model_path = f"modeling/models/{id}.model"
        return os.path.exists(model_path)

    def load(self):
        id = self.defn.exportableDescriptor()
        model_path = f"modeling/models/{id}.model"
        if not os.path.exists(model_path):
            raise Exception(f"Model specified by parameters {id} does not exist. Please train and save it.")
        
        checkpoint = torch.load(model_path)
        model = checkpoint['model']
        optimizer = checkpoint['optimizer']

        return model, optimizer
    
    def train(self):
        id = self.defn.exportableDescriptor()

        # save parameters for reference
        if not self.defn.fileAlreadyExists():
            self.defn.saveToFile(toJson=True)

        # instantiate model from parameters
        model = self.defn.generateModule()
        # TODO: makce an enum for controlling this, leave as default for now
        optimizer = torch.optim.Adam(model.parameters())

        # TODO: The code below is specific to a PyTorchDataSet. Look into AutoTS/other libraries
        # to see how this might be made generic
        # preprocess it so that we can input it into our training/testing
        # X is of the shape [#time series, #data points in each, #features at each point]
        self.dataset, self.testset = self.defn.dataset.get()
        dataset_size = len(self.dataset)

        # train model on the data
        model.train()

        train_dataloader = torch.utils.data.DataLoader(self.dataset, batch_size=self.defn.train_batch_size)
        batches = dataset_size // self.defn.train_batch_size
        for epoch in range(self.defn.epochs):
            batch_count = 0
            epoch_start = datetime.now()
            for batch in train_dataloader:
                batch_start = datetime.now()
                batch_coeffs, batch_y = batch
                pred_y = model(batch_coeffs)
                batch_y_norms = torch.tensor([[max(i.norm(), 1)] for i in batch_y[:,]]).transpose(1, -1)
  
                # weight = 
                # loss = torch.nn.functional.l1_loss(pred_y / batch_y_norms, batch_y / batch_y_norms)
                # TODO: need to let this function know about decomposition, but hardcoding it for now assuming one output
                loss = None
                if pred_y.size(1) == 1:
                    loss_func = CustomLoss()
                    loss = loss_func(pred_y, batch_y) #torch.nn.functional.mse_loss(pred_y, batch_y)
                else:
                    loss_func1 = CustomLoss(0.01)
                    loss_func2 = CustomLoss(0.01)
                    # print("means", pred_y[:,0], batch_y[:,0])
                    mean_loss = loss_func1(pred_y[:,0], batch_y[:,0])
                    # print("noise",pred_y[:,1], batch_y[:,1] )
                    noise_loss = loss_func2(pred_y[:,1], batch_y[:,1])
                    
                    
                    loss = mean_loss + 0.2 * noise_loss

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
            _, self.testset = self.defn.dataset.get()
       
        model.eval()
        test_X, test_y = self.testset[:]
        print("Testing dataset size", test_X.size())
        pred_y = model(test_X)

        prediction_miss = (pred_y - test_y)
        mags = []
        miss_mags = []
        for i, test in enumerate(test_y):
            mags.append(test.norm())
        for i, miss in enumerate(prediction_miss):
            miss_mags.append(miss.norm())
        classes = {}
        for miss_mag, mag in zip(miss_mags, mags):
            cls = -99 if mag == 0 else int(math.log(mag, 2))
            if not cls in classes:
                classes[cls] = {"ratio":[], "total": []}
            classes[cls]["ratio"].append(1 if mag == 0 else miss_mag/mag)
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
        average_miss_mag = sum([1 if mags[i] == 0 else miss_mags[i]/ mags[i] for i in range(len(mags))]) / len(mags)
        print(f"avg_miss_ratio: {average_miss_mag}")
        print(f"miss norm:", prediction_miss.norm())