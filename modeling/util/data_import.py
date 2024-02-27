import torch
from datetime import datetime, timedelta
import random

# Required: first column in the csv must be a datetime
def importData(filename, frame_size = 100, maximum_frames = 0, overlap = 0.25):
    frames = []
    data = {}
    columns = []
    stats = {}
    with open(filename, "r") as csv:
        prev_time = None
        time = 0
        for line in csv:
            record = line.split(",")
            if len(columns) == 0:
                columns = record
                for column in columns:
                    data[column] = []
                    stats[column] = {'sum': 0, 'count': 0}
            else:
                datetime_object = datetime.strptime(record[0], '%Y-%m-%d %H:%M:%S.%f')
                if prev_time is not None:
                    time += ((datetime_object - prev_time)/timedelta(microseconds=1)) / 1000.0
                prev_time = datetime_object
                if '(null)' in record:
                    break
                entries = zip(columns, [time] + [float(x) for x in record[1:]])
                for col, val in entries:
                    data[col].append(val)
                    if not 'min' in stats[col]:
                        stats[col]['min'] = val
                    stats[col]['min'] = min(stats[col]['min'], val)
                    if not 'max' in stats[col]:
                        stats[col]['max'] = val
                    stats[col]['max'] = max(stats[col]['max'], val)
                    stats[col]['sum'] += val
                    stats[col]['count'] += 1

                if len(data[columns[0]]) >= frame_size:
                    # TODO add line to optionally draw the frame using plt
                    frames.append(data)
                    data = {}
                    for column in columns:
                        data[column] = []

                    if overlap != 0:
                        for column in columns:
                            copy_index = int(len(data[column]) * (1.0 - overlap))
                            copy_index = max(1, copy_index)
                            data[column] = frames[-1][column][copy_index:]

                        # shift the time points down when we copy from the previous frame
                        first_t = data[columns[0]][0]
                        data[columns[0]] = [t - first_t for t in data[columns[0]]]
                        time = data[columns[0]][-1]

                if maximum_frames != 0 and len(frames) >= maximum_frames:
                    break

    # for col in stats:
    #     print(f"Col: {col} -- MIN: {stats[col]['min']} -- MAX: {stats[col]['max']} -- AVG: {stats[col]['sum'] / float(stats[col]['count'])}")
    # 1/0

    # normalize across all of the values
    for frame in frames:
        for col in frame:
            mi = stats[col]['min']
            ma = stats[col]['max']
            if mi == ma:
                ma += 1
            frame[col] = [(float(val) - mi) / (ma-mi) for val in frame[col]]
    split_index = int(len(frames) * 0.8)
    return frames[:split_index], frames[split_index:]

def getDataForTraining(dataset, time_dimension, inputs, outputs):
    c_dims = [time_dimension] + inputs
    tensor_frames = []
    y = []
    for frame in dataset:
        tensor_frames.append(torch.stack([torch.tensor(frame[c_dim]) for c_dim in c_dims], dim=1))
        y.append(torch.tensor([frame[output][-1] for output in outputs]))
    
    # The prediction label is the y value of the next step in the timeseries.
    # The last x value of the timeseries doesn't have a corresponding y, so we throw it out.
    tensor_frames = tensor_frames[:-1]
    y = y[1:]

    # Shuffle the data, training and prediction shouldn't depend on order.
    rnd_ind = [i for i in range(len(tensor_frames))]
    random.shuffle(rnd_ind)
    tensor_frames = [tensor_frames[i] for i in rnd_ind]
    y = [y[i] for i in rnd_ind]

    X = torch.stack(tensor_frames)
    y = torch.stack(y)
    return X, y