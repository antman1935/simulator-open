from util.Exportable import Exportable, ExportableType
import pandas as pd

"""
This class represents a source of data that can produce data usable by our DataSet class.
It produces a set of dataframes, each dataframe having the following qualities:
    * The given self.time_col column is the DateTime index for frame.
    * Originally, there were no gaps longer than self.gap_ms milliseconds.
    * The frame is resampled to have self.freq_ms milliseconds between each datapoint.
"""
class DataSource(Exportable):
    def __init__(self, time_col: str, min_frame_size: int, gap_ms: int = 3000, freq_ms: int = 1000):
        assert gap_ms > 0, "The maximum gap between records must be positive"
        assert min_frame_size > 0, "The minimum frame size has to be > 0"
        self.time_col = time_col
        self.min_frame_size = min_frame_size
        self.gap_ms = gap_ms
        self.freq_ms = freq_ms

    
    def getExportType(self) -> ExportableType:
        return ExportableType.DataSource
    
    """
    This method should be overloaded to return a Pandas dataframe.
    NOTE: Do not actually set the column to be the index in the returned
    dataframe. That is done in the DataSource subclass.
    """
    def loadData(self) -> pd.DataFrame:
        raise Exception("Unimplemented")
    
    """
    Split the single dataframe returned by subclass of DataSource into 
    multiple dataframes so that there are no large gaps and each dataframe
    is resampled to the desired frequency.
    """
    def loadDataFrames(self) -> list[pd.DataFrame]:
        import util.progress as progress
        df = self.loadData()
        df = df.assign(**{"time_diff": df[self.time_col].diff()})
        df.fillna({"time_diff": pd.Timedelta(0, 'sec')}, inplace=True)

        
        time_slices = df[self.time_col][df["time_diff"] > pd.Timedelta(self.gap_ms, 'millisecond')]
        df.drop('time_diff', axis='columns', inplace=True)
        print(f"{time_slices.size} gaps detected. Splitting dataframes.")

        begin_idx = df.first_valid_index()
        dfs = []
        rows_kept = 0
        thrown_away = 0
        rows_thrown_away = 0
        for i in range(time_slices.size):
            time = time_slices.iat[i]
            next_idx = df[df[self.time_col] == time].idxmin()[self.time_col]
            size = df[begin_idx:next_idx].size

            if size > self.min_frame_size:
                # print(f"Keeping records between {df[begin_idx][self.time_col]} - {df[next_idx][self.time_col]}")
                dfs.append(df[begin_idx:next_idx])
                rows_kept += dfs[-1].size
            else:
                # print(f"Tossing records between {df[begin_idx][self.time_col]} - {df[next_idx][self.time_col]}")
                thrown_away += 1
                rows_thrown_away += size
            progress.bar(i+1, time_slices.size)
            begin_idx = df[df[self.time_col] > time].idxmin()[self.time_col]

        print(f"Finished splitting data frames. {len(dfs)} with {rows_kept} total rows. {thrown_away} dataframes - {rows_thrown_away} rows thrown away.")

        print("Resampling for uniform time_steps")
        for i in range(len(dfs)):
            # now resample so that our time freq is always 1 second
            dfs[i].set_index(self.time_col, inplace=True)
            dfs[i] = dfs[i].resample(f"{self.freq_ms}ms").nearest()
            dfs[i] = (dfs[i] - dfs[i].min()) / (dfs[i].max() - dfs[i].min())
            progress.bar(i, len(dfs) - 1)
        
        return dfs
    
    def export_keys(self) -> list[dict]:
        running = super().export_keys()
        running.append(
          {
            "time_col": self.time_col,
            "min_frame_size": self.min_frame_size,
            "gap_ms": self.gap_ms,
            "freq_ms": self.freq_ms,
          }
        )
        return running