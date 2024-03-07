import pandas as pd
import matplotlib.pyplot as plt
import math
import sys, os
import torch
import torchcde

"""
This contains classes for manipulating a set of timeseries in csv format.
"""

def plot(dfs: list[pd.DataFrame], columns: list[str]):
    f = plt.figure()
    figs = len(columns)
    cols = 2
    rows = math.ceil(figs / cols)

    plots = [f.add_subplot(int(f"{rows}{cols}{i}")) for i in range(1, len(columns) + 1)]

    for plot, column in zip(plots, columns):
        plot.set_ylabel(column)
        plot.set_xlabel('Time')

    for df in dfs:
        for i, column in enumerate(columns):
            plot = plots[i]
            plot.plot(df[column])

    plt.show()


def read_csv(name, frame_length, gap_sec = 3):
    import util.progress as progress
    df = pd.read_csv(name, low_memory=False)
    print(f"Initial dataset size: {df.size} rows")

    # drop unnecessary columns
    df.drop(['wwResolution', 'Mixer100_MixingTime_SP'], axis='columns', inplace=True)

    # filter out null values at the beginning and end
    df.dropna(inplace=True)
    # print("Orig", df.size)
    # df = df[df != 'NaN']
    # print("Post", df.size)
    # df = df[df == torch.nan]
    # print("PostPost", df.size)
    # TODO: customize filtering and data cleaning
    # TODO: Throw out all columns that are constant
    df = df[df['Mixer100_Temperature_PV'] >= 120]
    print(f"Filtering done. {df.size} rows remaining.")

    # convert datetimes, and create datetime index
    df['DateTime'] = pd.to_datetime(df["DateTime"])

    df = df.assign(**{"time_diff": df["DateTime"].diff()})
    df.fillna(pd.Timedelta(0, 'sec'), inplace=True)

    
    time_slices = df['DateTime'][df["time_diff"] > pd.Timedelta(gap_sec, 'sec')]
    df.drop('time_diff', axis='columns', inplace=True)
    print(f"{time_slices.size} gaps detected. Splitting dataframes.")

    begin_idx = df.first_valid_index()
    dfs = []
    rows_kept = 0
    thrown_away = 0
    rows_thrown_away = 0
    for i in range(time_slices.size):
        time = time_slices.iat[i]
        next_idx = df[df["DateTime"] == time].idxmin()["DateTime"]
        size = df[begin_idx:next_idx].size
        if size > frame_length:
            dfs.append(df[begin_idx:next_idx])
            rows_kept += dfs[-1].size
        else:
            thrown_away += 1
            rows_thrown_away += size
        progress.bar(i+1, time_slices.size)
        begin_idx = df[df["DateTime"] > time].idxmin()["DateTime"]

    print(f"Finished splitting data frames. {len(dfs)} with {rows_kept} total rows. {thrown_away} dataframes - {rows_thrown_away} rows thrown away.")

    print("Resampling for uniform time_steps")
    for i in range(len(dfs)):
        # now resample so that our time freq is always 1 second
        dfs[i].set_index('DateTime', inplace=True)
        dfs[i] = dfs[i].resample('1s').nearest()
        dfs[i] = (dfs[i] - dfs[i].min()) / (dfs[i].max() - dfs[i].min())
        progress.bar(i, len(dfs) - 1)
    
    # plot(dfs, ['Mixer100_Level_PV', 'Mixer100_Temperature_PV'])

    return dfs

# TODO: more decomposition functionality
def create_datasets(dfs: list[pd.DataFrame], input_features, output_features, decompose = (False, 0), frame_size = 100, overlap = 0.25, maximum_frames = 0):
    import util.progress as progress
    decomp, window_size = decompose
    outputs = []
    if not decomp:
        outputs = output_features
    else:
        for output_feature in output_features:
            outputs.append(f"{output_feature}-{window_size}-MA")
            outputs.append(f"{output_feature}-noise")
    X = []
    y = []
    print("Converting dataframes to timeseries datapoints for training")
    for i in range(len(dfs)):
        if decomp:
            # decome each output feature as a rolling average and 
            for output_feature in output_features:
                mean_feat = f"{output_feature}-{window_size}-MA"
                noise_feat = f"{output_feature}-noise"
                dfs[i] = dfs[i].assign(**{mean_feat: (dfs[i][output_feature].rolling(window_size).mean())})
                dfs[i] = dfs[i].assign(**{noise_feat: dfs[i][output_feature] - dfs[i][mean_feat]})
                dfs[i].dropna(inplace=True)
        
        dfs[i].dropna(inplace=True)

        copy_size = int(overlap * frame_size)
        copy_size = max(copy_size, frame_size - 1)
        # label every sequence of X coordinates with the y coordinate one step in the future. 
        # Throw out the last x value because it has no label.
        for j in range(frame_size-1, dfs[i].index.size-1):
            y_df = dfs[i].at_time(dfs[i].index[j+1])[outputs]
            x_df = dfs[i][dfs[i].index[j-frame_size + 1]:dfs[i].index[j]][input_features]
            X.append(torch.concat((torch.tensor([[i / float(frame_size)] for i in range(frame_size)]), torch.tensor(x_df.values)), 1).float())
            y.append(torch.tensor(y_df.values).transpose(0, 1).squeeze(-1).float())

            if overlap > 0:
                j -= (copy_size - 1)

        progress.bar(i, len(dfs) - 1)


    X = torch.stack(X)
    y = torch.stack(y)
    # TODO: add torchcde calls as an option
    # X = torchcde.hermite_cubic_coefficients_with_backward_differences(X)

    throw_away = 0
    if maximum_frames > 0:
        throw_away = (X.size(0) - maximum_frames)/ X.size(0)

    split = [(1.0-throw_away) * 0.8, (1.0-throw_away) * 0.2, throw_away]
    print("Ratio (train/test/throwout)", split)
    
    [train, test, _] =  torch.utils.data.random_split(torch.utils.data.TensorDataset(X, y), [(1.0-throw_away) * 0.8, (1.0-throw_away) * 0.2, throw_away])
    return train, test
        




if __name__ == "__main__":
    sys.path.append(os.getcwd())
    dfs = read_csv('mixer simulation dataset.csv', frame_length=15)
    create_datasets(dfs, 
                        input_features= ['Mixer100_Inlet1_Position',
                                'Mixer100_Inlet2_Position',
                                'Mixer100_Outlet_Position',
                                'Mixer100_Level_PV',
                                'Mixer100_Temperature_PV'],
                        output_features= ['Mixer100_Temperature_PV'],
                        decompose= (True, 5),
                        frame_size= 8,
                        overlap=0.99)