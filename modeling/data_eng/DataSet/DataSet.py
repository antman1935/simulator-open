from modeling.data_eng.DataSource.DataSource import DataSource
from util.Exportable import Exportable, ExportableType
import pandas as pd
import pickle
import os

"""
This class takes a DataSource and transforms it into a form usable for training
neural network models.
"""
class DataSet(Exportable):
    _path = "modeling/datasets"
    def __init__(self, source: DataSource, persist: bool = False):
        self.source = source
        self.persist = persist
    
    def getExportType(self) -> ExportableType:
        return ExportableType.DataSet
    
    """
    Format the data so that it can be fed into a training algorithm. 
    Override this method to apply a transformation. This method determines
    the return type of the get() method.
    """
    def formatData(self, frames: list[pd.DataFrame]):
        raise Exception("Unimplemented")
    
    def get(self):
        id = self.exportableDescriptor()
        # save config to file if not already there.
        if not self.fileAlreadyExists():
            self.saveToFile(toJson=True)

        if self.persist:
            path = f"{DataSet._path}/{id}.ds"
            if os.path.exists(path):
                with open(path, "rb") as openfile:
                    formatted_data = pickle.load(openfile)
                return formatted_data
            
        frames = self.source.loadDataFrames()
        formatted_data = self.formatData(frames)

        if self.persist:
            path = f"{DataSet._path}/{id}.ds"
            with open(path, "wb+") as outfile:
                pickle.dump(formatted_data, outfile)

        return formatted_data
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "datasource": self.source.exportableDescriptor(),
          }
        )
        return running
    
if True:
    from pathlib import Path
    Path(DataSet._path).mkdir(parents=True, exist_ok=True)