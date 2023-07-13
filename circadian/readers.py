# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/05_readers.ipynb.

# %% auto 0
__all__ = ['VALID_WEREABLE_STREAMS', 'JSON_SCHEMA', 'EXAMPLE_DATA', 'wearable_schema', 'WereableAccessor', 'load_json',
           'load_csv', 'combine_wereable_dataframes', 'WereableData_NEW', 'WearableData', 'combine_wearable_streams',
           'read_standard_csv', 'read_standard_json', 'read_actiwatch']

# %% ../nbs/api/05_readers.ipynb 4
import json
import jsonschema
import numpy as np
import pandas as pd
from typing import Dict

# %% ../nbs/api/05_readers.ipynb 5
VALID_WEREABLE_STREAMS = ['steps', 'heartrate', 'wake', 'light_estimate', 'activity']

# %% ../nbs/api/05_readers.ipynb 6
@pd.api.extensions.register_dataframe_accessor("wereable")
class WereableAccessor:
    def __init__(self, pandas_obj):
        self._validate_columns(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate_columns(obj):
        if 'datetime' not in obj.columns:
            raise AttributeError("DataFrame must have 'datetime' column.")

        if not any([col in obj.columns for col in VALID_WEREABLE_STREAMS]):
            raise AttributeError(f"DataFrame must have at least one wereable data column from: {VALID_WEREABLE_STREAMS}.")
        
    @staticmethod
    def _validate_metadata(metadata):
        if not isinstance(metadata, dict):
            raise AttributeError("Metadata must be a dictionary.")
        if not any([key in metadata.keys() for key in ['data_id', 'subject_id']]):
            raise AttributeError("Metadata must have at least one of the following keys: data_id, subject_id.")
        if not all([isinstance(value, str) for value in metadata.values()]):
            raise AttributeError("Metadata values must be strings.")
    
    def is_valid(self):
        "Check if the dataframe is valid"
        self._validate_columns(self._obj)
        self._validate_metadata(self._obj.attrs)
        return True

    def add_metadata(self,
                     metadata: Dict[str, str], # metadata containing data_id, subject_id, or other_info
                     inplace: bool = False, # whether to return a new dataframe or modify the current one
                     ):
        "Add metadata to the dataframe"
        self._validate_metadata(metadata)
        if inplace:
            for key, value in metadata.items():
                self._obj.attrs[key] = value
        else:
            obj = self._obj.copy()
            for key, value in metadata.items():
                obj.attrs[key] = value
            return obj

    def plot(self, 
             name: str, # name of the wereable data to plot (one of steps, heartrate, wake, light_estimate, or activity)
             ax=None, # matplotlib axes
             *args, # arguments to pass to matplotlib.pyplot.plot
             **kwargs # keyword arguments to pass to matplotlib.pyplot.plot
             ):
        "Plot wereable data"
        if name not in VALID_WEREABLE_STREAMS:
            raise AttributeError(f"Name must be one of: {VALID_WEREABLE_STREAMS}.")
        if ax is None:
            ax = self._obj.plot(x='datetime', y=name, *args, **kwargs)
        else:
            ax = self._obj.plot(x='datetime', y=name, ax=ax, *args, **kwargs)
        return ax

# %% ../nbs/api/05_readers.ipynb 11
JSON_SCHEMA = {
    type: "object",
    "properties": {
            "steps": {
                "type": "array",
                "items": { "type": "object", "properties": { 
                    "start": { "type": "number" },
                    "end": { "type": "number" },
                    "steps": { "type": "number" } } },
                "minItems": 1
            },
            "wake": {
                "type": "array",
                "items": { "type": "object", "properties": { 
                    "start": { "type": "number" },
                    "end": { "type": "number" },
                    "wake": { "type": "number" } } }
            },
            "heartrate": {
                "type": "array",
                "items": { "type": "object", "properties": { 
                    "timestamp": { "type": "number" },
                    "heartrate": { "type": "number" },
            } } },
    },
    "required": ["steps", "wake", "heartrate"]
}

# %% ../nbs/api/05_readers.ipynb 12
def load_json(filepath: str, # path to file
              metadata: Dict[str, str] = None, # metadata containing data_id, subject_id, or other_info
              ) -> Dict[str, pd.DataFrame]: # dictionary of wereable dataframes
    "create a dataframe from a json containing wereable data"
    if not isinstance(filepath, str):
        raise AttributeError("Filepath must be a string.")

    jdict = json.load(open(filepath, 'r'))
    # jsonschema.validate(jdict, schema=JSON_SCHEMA) # TODO: check for a better option, this is VERY slow
    # check that keys are valid
    for key in jdict.keys():
        if key not in VALID_WEREABLE_STREAMS:
            raise AttributeError("Invalid key in JSON file. Keys must be one of steps, heartrate, wake, light_estimate, or activity.")
    # create a df for each key
    df_dict = {key: pd.DataFrame.from_dict(jdict[key]) for key in jdict.keys()}
    for key in df_dict.keys():
        df = df_dict[key]
        if key == 'heartrate':
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        else:
            df['datetime'] = pd.to_datetime(df['start'], unit='s')
            df = df.rename(columns={'start': f'{key}_start', 'end': f'{key}_end'})
        if metadata is not None:
            df.wereable.add_metadata(metadata, inplace=True)
        else:
            df.wereable.add_metadata({'data_id': 'unknown', 'subject_id': 'unknown'}, inplace=True)
        df_dict[key] = df
    return df_dict

# %% ../nbs/api/05_readers.ipynb 14
def load_csv(filepath: str, # full path to csv file to be loaded
             metadata: Dict[str, str] = None, # metadata containing data_id, subject_id, or other_info
             timestamp_col: str = None, # name of the column to be used as timestamp. If None, it is assumed that a `datetime` column exists
             *args, # arguments to pass to pd.read_csv
             **kwargs, # keyword arguments to pass to pd.read_csv
             ):
    "Create a dataframe from a csv containing wereable data"
    df = pd.read_csv(filepath, *args, **kwargs)
    if timestamp_col is not None:
        df['datetime'] = pd.to_datetime(df[timestamp_col], unit='s')
    if metadata is not None:
        df.wereable.add_metadata(metadata, inplace=True)
    else:
        df.wereable.add_metadata({'data_id': 'unknown', 'subject_id': 'unknown'}, inplace=True)
    return df

# %% ../nbs/api/05_readers.ipynb 18
def combine_wereable_dataframes(
        df_dict: Dict[str, pd.DataFrame], # dictionary of wereable dataframes
        metadata: Dict[str, str] = None, # metadata containing for the combined dataframe
        resample: bool = False, # whether to resample the data
        resample_freq: str = '6T', # resampling frequency (e.g. '6T' for 6 minutes)
        ) -> pd.DataFrame: # combined wereable dataframe
    "combine a dictionary of wereable dataframes into a single dataframe"
    df_list = []
    for name in df_dict.keys():
        df = df_dict[name]
        df.wereable.is_valid()
        if resample:
            if name == 'heartrate' or name == 'light_estimate':
                resampled_df = df.resample(
                                    resample_freq, on='datetime'
                                ).agg(WEREABLE_RESAMPLE_METHOD[name])
                resampled_df.reset_index(inplace=True)
            else:
                # TODO: deal with data streams that have start and end times
                # ... 
                '''
                # for example
                s1 = steps.loc[:, ['start', 'steps']]
                s2 = steps.loc[:, ['end', 'steps']]
                s1.rename(columns={'start': 'timestamp'}, inplace=True)
                s2.rename(columns={'end': 'timestamp'}, inplace=True)
                steps = pd.concat([s1, s2])
                steps.set_index('timestamp', inplace=True)
                steps = steps.resample(str(int(bin_minutes)) +
                                    'Min').agg({'steps': 'sum'})
                steps.reset_index(inplace=True)
                '''
                pass
        df_list.append(resampled_df)
    # join all dfs by datetime
    df = df_list[0]
    for i in range(1, len(df_list)):
        df = df.merge(df_list[i], on='datetime', how='outer')
    # add metadata
    if metadata is not None:
        df.wereable.add_metadata(metadata, inplace=True)
    else:
        df.wereable.add_metadata({'data_id': 'combined_dataframe'}, inplace=True)
    return df

# %% ../nbs/api/05_readers.ipynb 22
import os
import json
import gzip
import glob 
import random
import difflib
import circadian
import numpy as np
import pylab as plt
import pandas as pd
from os import read
from pathlib import Path
from copy import deepcopy
from .utils import *
from datetime import datetime
from jsonschema import validate
from dataclasses import dataclass
from scipy.stats import linregress
from fastcore.basics import patch_to
from .plots import Actogram
from scipy.ndimage import gaussian_filter1d
from typing import List, Tuple, Dict, Union, Optional, Any, Callable, Iterable

pd.options.mode.chained_assignment = None

# %% ../nbs/api/05_readers.ipynb 23
EXAMPLE_DATA = circadian.__path__[0]

# %% ../nbs/api/05_readers.ipynb 24
wearable_schema = {
    type: "object",
    "properties": {
            "steps": {
                "type": "array",
                "items": { "type": "object", "properties": { 
                    "start": { "type": "number" },
                    "end": { "type": "number" },
                    "steps": { "type": "number" } } },
                "minItems": 1
            },
            "wake": {
                "type": "array",
                "items": { "type": "object", "properties": { 
                    "start": { "type": "number" },
                    "end": { "type": "number" },
                    "wake": { "type": "number" } } }
            },
            "heartrate": {
                "type": "array",
                "items": { "type": "object", "properties": { 
                    "timestamp": { "type": "number" },
                    "heartrate": { "type": "number" },
            } } },
    },
    "required": ["steps", "wake", "heartrate"]
}

# %% ../nbs/api/05_readers.ipynb 30
class WereableData_NEW:
    "Helper class for working with wereable data"
    def __init__(self,
                 dataframe: pd.DataFrame, # Required columns: datetime, wereable-data (one of steps, heartrate, wake, light_estimate, or activity)
                 data_id: str="unknown-data-id", # Unique identifier for the data
                 subject_id: str="unknown-subject", # Unique subject identifier
                 meta_data: Dict[str, Any]=None # Additional information about the dataset
                 ):
        self._dataframe = dataframe
        self._data_id = data_id
        self._subject_id = subject_id
        self._meta_data = meta_data

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._dataframe
    
    @dataframe.setter
    def dataframe(self, value):
        # check that dataframe is the correct type and has the required columns
        self._dataframe = value

    @property
    def data_id(self) -> str:
        return self._data_id

    @data_id.setter
    def data_id(self, value):
        # check that it is a string
        self._data_id = value

    @property
    def subject_id(self) -> str:
        return self._subject_id
    
    @subject_id.setter
    def subject_id(self, value) -> str:
        # check that it is a string
        self._subject_id = value

    @property
    def meta_data(self) -> Dict[str, Any]:
        return self._meta_data

    @meta_data.setter
    def meta_data(self, value):
        # check it is a dict
        self._meta_data = value
    

# %% ../nbs/api/05_readers.ipynb 32
@patch_to(WereableData_NEW)
def from_json(self,
              filepath: str, # path to file
              ):
    "Create a WereableData object from a json"
    # check that filepath is a str
    # load json
    # check json schema
    # create dataframe
    # create object and return it
    jdict = json.load(open(filepath, 'r'))
    df = pd.DataFrame.from_dict(jdict['wearable']) 
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    return WearableData_NEW(df)

# %% ../nbs/api/05_readers.ipynb 33
@patch_to(WereableData_NEW)
def from_csv(self,
             filepath: str, # path to file
             ):
    "Create a WereableData object from a csv file"
    # load csv into a dataframe
    # check required fields
    # create object and return it
    pass

# %% ../nbs/api/05_readers.ipynb 34
#TODO: Do we need this or it can be read as a csv???
@patch_to(WereableData_NEW)
def from_actiwatch(self,
                   filepath: str, # path to file
                   ):
    "Create a WereableData object from an actiwatch record file"
    # load file into a dataframe
    # check required fields
    # create object and return it
    pass

# %% ../nbs/api/05_readers.ipynb 35
@patch_to(WereableData_NEW)
def to_json(self, 
            filepath: str, # path to file
            filename: str, # filename without .json
            ):
    "Save a WereableData object as a json"
    # TODO: check Kevin's implementation
    pass

# %% ../nbs/api/05_readers.ipynb 38
@dataclass
class WearableData:
    _dataframe: pd.DataFrame # the dataframe that holds the data must have datetime columns plus any other wearable streams from steps, heartrate, wake, light_estimate, activity
    phase_measure: np.ndarray = None
    phase_measure_times: np.ndarray = None
    subject_id: str = "unknown-subject"
    data_id: str = "unknown-data-id"
    meta_data: Dict[str, Any] = None
    
    @property
    def datetime(self) -> np.ndarray:
        return self._dataframe["datetime"].values
    
    @property
    def timestamp(self) -> np.ndarray:
        return self._dataframe["timestamp"].values
    
    @property
    def time_total(self) -> np.ndarray:
        return self._dataframe["time_total"].values
    
    @property
    def light_estimate(self) -> np.ndarray:
        if 'light_estimate' in self._dataframe.columns:
            return self._dataframe["light_estimate"].values
        if 'steps' in self._dataframe.columns:
            return self._dataframe["steps"].values
        if 'activity' in self._dataframe.columns:
            return self._dataframe["activity"].values
        return np.ones_like(self.time_total)*np.nan
    
    @property
    def steps(self) -> np.ndarray:
        if 'steps' in self._dataframe.columns:
            return self._dataframe["steps"].values
        else:
            return np.ones_like(self.time_total)*np.nan
    
    @property
    def activity(self) -> np.ndarray:
        if 'activity' in self._dataframe.columns:
            return self._dataframe["activity"].values
        else:
            return np.ones_like(self.time_total)*np.nan
    
    @property
    def heartrate(self) -> np.ndarray:
        if 'heartrate' in self._dataframe.columns:
            return self._dataframe["heartrate"].values
        else:
            return np.ones_like(self.time_total)*np.nan # generate a nan array
    
    @property
    def wake(self) -> np.ndarray:
        if 'wake' in self._dataframe.columns:
            return self._dataframe["wake"].values
        else:
            return np.ones_like(self.time_total)*np.nan # generate a nan array
        
    @property
    def time_hour_bounds(self) -> Tuple[float, float]:
        return (self.time_total[0], self.time_total[-1])
    
    @property
    def date_bounds(self):
        start_date = pd.to_datetime(self.datetime[0], unit='s')
        end_date = pd.to_datetime(self.datetime[-1], unit='s')
        return (start_date, end_date)
    
    @staticmethod
    def utc_to_hrs(d: datetime):
        return d.hour+d.minute/60.0+d.second/3600.0

    def __post_init__(self):
        # Check that we have the required columns
        assert "datetime" in self._dataframe.columns
        assert "time_total" in self._dataframe.columns
        
    def _copy_with_metadata(self, df: pd.DataFrame) -> "WearableData":
        return WearableData(df, 
                            self.phase_measure, 
                            self.phase_measure_times, 
                            self.subject_id, 
                            self.data_id, 
                            meta_data=self.meta_data)

    def build_sleep_chunks(self, chunk_jump_hrs: float = 12.0) -> List[np.ndarray]:
        time_total = self.time_total
        steps = self.steps
        heartrate = self.heartrate
        wake = self.wake
        data = np.stack((steps, heartrate, wake), axis=0)
        j_idx = np.where(np.diff(time_total) > chunk_jump_hrs)[0]
        return np.split(data, j_idx, axis=1)

    def get_date(self, time_hr: float):
        idx = np.argmin(np.abs(np.array(self.time_total) - time_hr))
        return pd.to_datetime(self.datetime[idx], unit='s')

    def get_timestamp(self, time_hr: float):
        idx = np.argmin(np.abs(np.array(np.hstack(self.time_total)) - time_hr))
        return np.hstack(self.datetime)[idx]

    def trim_by_idx(self, 
                    idx1: int, # First index to keep
                    idx2: int = None # second idx should be greater than idx1, defaults to the last value
                    ) -> 'WearableData':
        df = self._dataframe.loc[idx1:idx2, :]
        return self._copy_with_metadata(df)

    def trim_by_hour(self, 
                     hour_start: float, # First hour to keep
                     hour_end: float, # second hour should be greater than hour_start
                     inplace: bool = False, # if true, the dataframe is modified in place, otherwise a copy is returned
                     ) -> 'WearableData':
        # Trim the __dateframe to be within the interval [t1,t2]
        df = self._dataframe.loc[(self._dataframe.time_total > hour_start) & (self._dataframe.time_total < hour_end)]
        if inplace:
            self._dataframe = df
            return 
        return self._copy_with_metadata(df)
    
    def trim_by_timestamp(self, timestamp_start: float, timestamp_end: float) -> 'WearableData':
        # Trim the __dateframe to be within the interval [t1,t2]
        df = self._dataframe.loc[(self._dataframe.datetime > timestamp_start) & (self._dataframe.datetime < timestamp_end)]
        return self._copy_with_metadata(df)
    
    def __getitem__(self, key: str) -> pd.Series:
        return self._dataframe[key]
        
    def head(self, n: int = 5) -> pd.DataFrame:
        return self._dataframe.head(n)
    
    def tail(self, n: int = 5) -> pd.DataFrame:
        return self._dataframe.tail(n) 
    
    def filter(self, filter_fn: Callable[[pd.DataFrame], pd.DataFrame]) -> 'WearableData':
        return self._copy_with_metadata(filter_fn(self._dataframe))
    
    def aggregate(self, agg_fn: Callable[[pd.DataFrame], pd.DataFrame]) -> 'WearableData':
        return self._copy_with_metadata(agg_fn(self._dataframe))
    
    def groupby(self, by: str) -> 'WearableData':
        return self._copy_with_metadata(self._dataframe.groupby(by))
    
    def join(self, other: 'WearableData', how = 'inner') -> 'WearableData':
        return self._copy_with_metadata(self._dataframe.join(other._dataframe, on='datetime', how=how))
    
    def to_json(self, filename: str = None):
        df_trimed = self._dataframe.drop(columns=['datetime'])
        json_dict = {
            'meta_data' : self.meta_data, 
            'phase_measure' : list(self.phase_measure) if self.phase_measure is not None else [],
            'phase_measure_times' : list(self.phase_measure_times) if self.phase_measure_times is not None else [],
            'subject_id' : self.subject_id,
            'data-id' : self.data_id,
            'wearable' : df_trimed.to_dict()
        }
        if filename is None:
            filename = 'wearable_' + self.subject_id + "_" + self.data_id + '.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False,
                        indent=4, cls = NpEncoder )

    @staticmethod
    def from_json(filename) -> 'WearableData':
        jdict = json.load(open(filename, 'r'))
        df = pd.DataFrame.from_dict(jdict['wearable']) 
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        wdata = WearableData(df)
        for s in jdict.keys():
            if s != 'wearable':
                if isinstance(jdict[s], list):
                    setattr(wdata, s, [np.array(jdict[s])])
                else:
                    setattr(wdata, s, jdict[s])

        return wdata

# %% ../nbs/api/05_readers.ipynb 39
@patch_to(WearableData)
def steps_hr_loglinear(self: WearableData
                       ) -> Tuple[float, float]:
        """
        Find the log steps to hr linear regression parameters .
        hr=beta*log(steps+1.0)+alpha
        Returns beta,alpha
        """
        x = np.log(np.hstack(self.steps)+1.0)
        y = np.hstack(self.heartrate)
        x = x[y > 0]
        y = y[y > 0]
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        return slope, intercept

# %% ../nbs/api/05_readers.ipynb 41
@patch_to(WearableData)
def plot_heartrate(self: WearableData, 
                   t1=None, 
                   t2=None, 
                   ax: plt.Axes = None,
                   show_plot: bool = True,
                   color: str = 'red', 
                   use_dates: bool = True,
                   *args, 
                   **kwargs
                   ) -> plt.Axes:
        t1 = t1 if t1 is not None else self.time_total[0]
        t2 = t2 if t2 is not None else self.time_total[-1]
        wDataTrimmed = self.trim_by_hour(t1, t2)

        hr = deepcopy(wDataTrimmed.heartrate)
        hr[hr == 0] = np.nan
        if ax is None:
            fig = plt.figure()
            ax = plt.gca()
        
        if use_dates:
            x = pd.to_datetime(wDataTrimmed.datetime, unit='s')
        else:
            x = wDataTrimmed.time_total / 24.0 
        ax.plot(x, hr, color=color, *args, **kwargs)
        ax.set_xlabel('Days')
        ax.set_ylabel('BPM')
        ax.set_title('Heart Rate Data')
        
        if show_plot:
            plt.show()
        return ax

# %% ../nbs/api/05_readers.ipynb 42
@patch_to(WearableData)
def scatter_hr_steps(self: WearableData, 
                     take_log: bool = True, # Log transform the data?
                     *args, 
                     **kwargs):
    
        fig = plt.figure()
        ax = plt.gca()

        steps = np.hstack(self.steps)
        heartrate = np.hstack(self.heartrate)

        if take_log:
            ax.scatter(np.log10(steps[heartrate > 0]+1.0),
                       np.log10(heartrate[heartrate > 0]),
                       color='red',
                       *args,
                       **kwargs)
        else:
            ax.scatter(steps[heartrate > 0], heartrate[heartrate > 0],
                       color='red',
                       *args,
                       **kwargs)

        ax.set_ylabel('BPM')
        ax.set_xlabel('Steps')
        ax.set_title('Heart Rate Data')
        plt.show()

# %% ../nbs/api/05_readers.ipynb 43
@patch_to(WearableData)
def plot_hr_steps(self: WearableData, 
                  t1: float = None, 
                  t2: float = None, 
                  *args, 
                  **kwargs):

        time_start = t1 if t1 is not None else self.time_total[0]/24.0
        time_end = t2 if t2 is not None else self.time_total[-1]/24.0

        fig = plt.figure()
        gs = fig.add_gridspec(2, hspace=0.0)
        ax = gs.subplots(sharex=True)
        fig.suptitle(
            f"{self.data_id} Wearable Data: Subject {self.subject_id}")
        hr_all_nan = np.all(np.isnan(self.heartrate))
        if not hr_all_nan:
            ax[0].plot(self.time_total / 24.0, 
                       self.heartrate, 
                       color='red', 
                       *args, 
                       **kwargs)
            
        ax[1].plot(self.time_total / 24.0, 
                   self.steps,
                   color='darkgreen', 
                   *args, 
                   **kwargs)

        sleep_all_nan = np.all(np.isnan(self.wake))
        if not sleep_all_nan:
            ax[1].plot(self.time_total / 24.0, np.array(self.wake) *
                       max(np.median(self.steps), 50.0), color='k')

        if self.phase_measure_times is not None:
            [ax[0].axvline(x=_x / 24.0, ls='--', color='blue')
             for _x in self.phase_measure_times]
            [ax[1].axvline(x=_x / 24.0, ls='--', color='blue')
             for _x in self.phase_measure_times]

        ax[1].set_xlabel("Days")
        ax[0].set_ylabel("BPM")
        ax[1].set_ylabel("Steps")
        ax[0].grid()
        ax[1].grid()
        ax[0].set_xlim((time_start, time_end))
        ax[1].set_xlim((time_start, time_end+3.0))
        ax[0].set_ylim((0, 200))
        plt.show()

# %% ../nbs/api/05_readers.ipynb 45
def combine_wearable_streams(steps: pd.DataFrame,  # dataframe with columns 'start', 'end', 'steps'
                             heartrate: pd.DataFrame,  # dataframe with columns 'timestamp', 'heartrate'
                             wake: pd.DataFrame,  # dataframe with columns 'start', 'end', 'wake'
                             bin_minutes: int = 6,  # bin size in minutes for the resampled combined data
                             subject_id: str = "unknown-subject",
                             data_id: str = "Exporter",
                             sleep_trim: bool = False,  # drop any entries without a sleep-wake entry
                             # if true, only keep entries that have both heartrate and sleep data
                             inner_join: bool = False
                             ) -> WearableData:

    # Convert unix times to datetime
    steps['start'] = pd.to_datetime(steps.start, unit='s')
    steps['end'] = pd.to_datetime(steps.end, unit='s')
    wake['start'] = pd.to_datetime(wake.start, unit='s')
    wake['end'] = pd.to_datetime(wake.end, unit='s')
    heartrate['timestamp'] = pd.to_datetime(heartrate.timestamp, unit='s')

    # Resample the steps to the desired bin size
    s1 = steps.loc[:, ['start', 'steps']]
    s2 = steps.loc[:, ['end', 'steps']]
    s1.rename(columns={'start': 'timestamp'}, inplace=True)
    s2.rename(columns={'end': 'timestamp'}, inplace=True)
    steps = pd.concat([s1, s2])
    steps.set_index('timestamp', inplace=True)
    steps = steps.resample(str(int(bin_minutes)) +
                           'Min').agg({'steps': 'sum'})
    steps.reset_index(inplace=True)

    # Resample the heartrate data to the desired bin size
    heartrate.set_index('timestamp', inplace=True)
    heartrate = heartrate.resample(
        str(int(bin_minutes))+'Min').agg({'heartrate': 'max'})
    heartrate.reset_index(inplace=True)

    # Merge the steps and heartrate data and fill missing heartrate with zeros
    merge_method = 'inner' if inner_join else 'left'
    df = pd.merge(steps, heartrate, on='timestamp', how=merge_method)

    # Resample the wake data to the desired bin size
    s1 = wake.loc[:, ['start', 'wake']]
    s2 = wake.loc[:, ['end', 'wake']]
    s1.rename(columns={'start': 'timestamp'}, inplace=True)
    s2.rename(columns={'end': 'timestamp'}, inplace=True)
    wake = pd.concat([s1, s2])
    wake.set_index('timestamp', inplace=True)
    wake = wake.resample(str(int(bin_minutes)) +
                         'Min').agg({'wake': 'max'})
    wake.reset_index(inplace=True)

    merge_method = 'inner' if inner_join else 'left'
    df = pd.merge(df, wake, on='timestamp', how=merge_method)

    df['datetime'] = df['timestamp']

    # Make the timestamp column actually be a unix timestamp
    df['timestamp'] = (
        df['datetime'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

    time_start = WearableData.utc_to_hrs(df.datetime.iloc[0])
    df['time_total'] = time_start + (df.timestamp-df.timestamp.iloc[0])/3600.0

    if sleep_trim:
        df.dropna(subset=['wake'], inplace=True)

    aw = WearableData(_dataframe=df,
                      subject_id=subject_id,
                      data_id=data_id
                      )

    return aw


def read_standard_csv(path: str,  # path to the directory containing the csv files
                      glob_str: str = "*.csv",  # glob to use to find the csv files
                      keyword: str = '', #entra filter to apply to the files for example a subject-id 
                      bin_minutes: int = 6,
                      subject_id="unknown-subject",
                      data_id="Exporter",
                      sleep_trim: bool = False,  # drop any entries without a sleep-wake entry
                      # if true, only keep entries that have both heartrate and sleep data
                      inner_join: bool = False
                      ) -> WearableData:
    candidate_files = list(filter(lambda x: keyword in x, glob.glob(path+"/"+glob_str)))
    steps_filelist = list(filter(lambda x: "steps" in x, candidate_files))
    heartrate_filelist = list(filter(lambda x: ("heartrate" in x) or ('hr' in x), candidate_files))
    sleep_filelist = list(filter(lambda x: "sleep" in x or 'wake' in x, candidate_files))
    if len(steps_filelist) > 0:
        print(f"Reading the steps file {steps_filelist[0]}")
        steps = pd.read_csv(steps_filelist[0], names=[
                            'start', 'end', 'steps'])
    if len(heartrate_filelist) > 0:
        print(f"Reading the heartrate file {heartrate_filelist[0]}")
        heartrate = pd.read_csv(heartrate_filelist[0], names=[
                                'timestamp', 'heartrate'])
    else:
        heartrate = pd.DataFrame(columns=['timestamp', 'heartrate'])
    if len(sleep_filelist) > 0:
        print(f"Reading the sleep file {sleep_filelist[0]}")
        wake = pd.read_csv(sleep_filelist[0], names=['start', 'end', 'wake'])
    else:
        wake = pd.DataFrame(columns=['start', 'end', 'wake'], dtype=float)

    if steps is None:
        raise ValueError("No steps file found, need to at least have that file")

    return combine_wearable_streams(steps, heartrate, wake, bin_minutes, subject_id, data_id, sleep_trim, inner_join)

# %% ../nbs/api/05_readers.ipynb 46
def read_standard_json(filepath: str,  # path to json file
                       bin_minutes: int = 6,  # data will be binned to this resolution in minutes
                       subject_id: str = "unknown-subject",  # subject id to be used
                       data_id: str = "Exporter",  # name of the data source
                       # set to true if the file is gzipped, will be autodetected if extension is .gz
                       gzip_opt: bool = False,
                       sleep_trim: bool = False,  # drop any entries without a sleep-wake entry
                       # if true, only keep entries that have both heartrate and sleep data
                       inner_join: bool = False
                       ) -> WearableData:
    gzip_opt = gzip_opt if gzip_opt else filepath.endswith(".gz")
    fileobj = gzip.open(filepath, 'r') if gzip_opt else open(filepath, 'r')
    rawJson = json.load(fileobj)
    validate(rawJson, wearable_schema)

    steps = pd.DataFrame(rawJson['steps'], columns=["start", "end", "steps"])
    # These could be empty
    wake = pd.DataFrame(rawJson['wake'], columns=["start", "end", "wake"])
    heartrate = pd.DataFrame(rawJson['heartrate'], columns=[
                             "timestamp", "heartrate"])

    return combine_wearable_streams(steps, heartrate, wake, bin_minutes, subject_id, data_id, sleep_trim, inner_join)

# %% ../nbs/api/05_readers.ipynb 47
@patch_to(WearableData)
def fillna(self: WearableData, 
             column_name: str = "heartrate", # column to fill in the dataframe
             with_value: float = 0.0, # value to fill with
             inplace: bool = False # if true, the WearableData object will be modified in place
             ) -> WearableData:
    
    if inplace:
        self._dataframe[column_name].fillna(with_value, inplace=True)
    else:
        df = self._dataframe.copy()
        filled_column = df[column_name].fillna(with_value)
        df[column_name] = filled_column 
        return self._copy_with_metadata(df)

# %% ../nbs/api/05_readers.ipynb 63
@patch_to(WearableData)
def plot_light_activity(self: WearableData, 
                        show=True, 
                        vlines=None, 
                        *args, **kwargs):

        fig = plt.figure()
        gs = fig.add_gridspec(2, hspace=0)
        ax = gs.subplots(sharex=True)
        fig.suptitle(
            f"{self.data_id} Subject {self.subject_id}")
        ax[0].plot(self.time_total / 24.0, np.log10(self.light_estimate+1.0), color='red')
        ax[1].plot(self.time_total / 24.0, self.activity, color='darkgreen')
        
        try:
            ax[1].plot(self.time_total / 24.0, self.wake *
                       np.median(self.steps), color='k')
        except:
            print(f"Error with wake plot with {self.subject_id}")

        if self.phase_measure_times is not None:
            [ax[0].axvline(x=_x / 24.0, ls='--', color='blue')
             for _x in self.phase_measure_times]
            [ax[1].axvline(x=_x / 24.0, ls='--', color='blue')
             for _x in self.phase_measure_times]

        if vlines is not None:
            [ax[0].axvline(x=_x / 24.0, ls='--', color='cyan')
             for _x in vlines]
            [ax[1].axvline(x=_x / 24.0, ls='--', color='cyan')
             for _x in vlines]

        ax[1].set_xlabel("Days")
        ax[0].set_ylabel("Lux (log 10)")
        ax[1].set_ylabel("Activity Counts")
        ax[0].grid()
        ax[1].grid()
        if show:
            plt.show()
        else:
            return ax

# %% ../nbs/api/05_readers.ipynb 65
def read_actiwatch(filepath: str, # path to actiwatch csv file
                   MIN_LIGHT_THRESHOLD=5000, # used to trim off empty data at the beginning and end of the file, must reach this amount of light to be included. Turn this off can setting this to 0 or negative 
                   round_data=True, # round the data to the nearest bin_minutes 
                   bin_minutes=6, # bin the data to this resolution in minutes, only used if round_data is true 
                   dt_format: str = None, # format of the date time string, if None, will be inferred 
                   data_id: str = "Actiwatch", # name of the data source 
                   subject_id: str = "unknown-subject", #subject id to be used
                   ) -> WearableData:
    
    df = pd.read_csv(filepath, names=['Date', 'Time', 'Activity', 'White Light', 'Sleep/Wake'], header=0) 
    df['datetime'] = df['Date']+" "+df['Time']
    if dt_format is None:
        df['datetime'] = pd.to_datetime(df.datetime)
    else:
        df['datetime'] = pd.to_datetime(df.datetime, format=dt_format)

    df['UnixTime'] = (
        df['datetime'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
    
    df.rename(columns={'White Light': 'light_estimate'}, inplace=True)
    df.rename(columns={'Sleep/Wake': 'wake'}, inplace=True)
    df.rename(columns={'Activity': 'activity'}, inplace=True)

    df['light_estimate'].fillna(0, inplace=True)
    df['LightSum'] = np.cumsum(df.light_estimate.values)
    df['LightSumReverse'] = np.sum(
        df.light_estimate.values) - np.cumsum(df.light_estimate.values) + 1.0

    df = df[(df.LightSum > MIN_LIGHT_THRESHOLD) & (
        df.LightSumReverse > MIN_LIGHT_THRESHOLD)]

    time_start = WearableData.utc_to_hrs(df.datetime.iloc[0])
    df2 = df[['UnixTime']].copy(deep=True)
    base_unix_time = df2['UnixTime'].iloc[0]
    df['time_total'] = time_start + \
        (df2.loc[:, ['UnixTime']]-base_unix_time)/3600.0
        
    df['timestamp'] = df['UnixTime']
    
    df = df[["datetime", "timestamp", "time_total", "activity", "light_estimate", "wake"]]
    if round_data:
        df.set_index('datetime', inplace=True)
        df = df.resample(str(int(bin_minutes))+'Min').agg({'time_total': 'min',
                                                            'activity': 'sum',
                                                            'light_estimate': 'median',
                                                            'wake': 'max'})
        df.reset_index(inplace=True)
    df['time_total'].interpolate(inplace=True)
    df.activity.fillna(0.0, inplace=True) 
    df.light_estimate.fillna(0.0, inplace=True)
    return WearableData(
        _dataframe = df,
        data_id=data_id,
        subject_id=subject_id
    )
