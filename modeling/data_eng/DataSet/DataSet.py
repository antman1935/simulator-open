from modeling.data_eng.DataSource.DataSource import DataSource
from util.Exportable import Exportable, ExportableType
import pandas as pd

"""
This class takes a DataSource and transforms it into a form usable for training
neural network models.
"""
class DataSet(Exportable):
    def __init__(self, source: DataSource):
        self.source = source
    
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
        frames = self.source.loadDataFrames()
        return self.formatData(frames)
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "datasource": self.source.exportableDescriptor(),
          }
        )
        return running