from modeling.data_eng.DataSource.DataSource import DataSource
import pandas as pd

"""
This class reads a csv exported from Aveva Historian and does some transformations to make a dataset.
"""
class AvevaHistorianDataSource(DataSource):
    def __init__(self, csv_name: str, series: list[str], min_frame_size: int, timestamp_series: str = "DateTime", gap_ms: int = 3000, freq_ms: int = 1000, persist: bool = False):
        super().__init__(timestamp_series, min_frame_size, gap_ms=gap_ms, freq_ms=freq_ms, persist=persist)
        self.csv_name = csv_name
        self.series = series
        self.series.append(timestamp_series)
    
    """
    Read in a csv and filter out some rows.
    """
    def loadData(self):
        df = pd.read_csv(self.csv_name, low_memory=False)
        print(f"Initial dataset size: {df.size} rows")

        # drop unnecessary columns
        df.drop([column for column in df.columns if not column in self.series], axis='columns', inplace=True)

        # filter out null values at the beginning and end
        df.dropna(inplace=True)

        # TODO: customize filtering and data cleaning
        # TODO: Throw out all columns that are constant
        df = df[df['Mixer100_Temperature_PV'] >= 120]
        print(f"Filtering done. {df.size} rows remaining.")

        df['DateTime'] = pd.to_datetime(df["DateTime"])
        return df
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "csv_name": self.csv_name,
            "series": self.series,
          }
        )
        return running