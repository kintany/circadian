# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_lights.ipynb.

# %% auto 0
__all__ = ['LightSchedule', 'make_pulse', 'get_pulse']

# %% ../nbs/01_lights.ipynb 3
import inspect
import warnings
import numpy as np
import pylab as plt
from typing import Callable
from fastcore.basics import patch_to
from numpy.core.fromnumeric import repeat

# %% ../nbs/01_lights.ipynb 4
class LightSchedule:
    "Helper class for creating light schedules"
    def __init__(self, 
                 light: float | Callable, # light function that takes in a time value and returns a float, if a float is passed, then the light function is a constant set to that lux value 
                 period: float = None, # period in hours, if None, then the light pulse is not repeated. Must be positive
                 ) -> None:
        # period input checking
        period_err_msg = "`period` should be a positive `float` or `int`"
        if period != None:
            if not isinstance(period, (int, float)):
                raise TypeError(period_err_msg)
            elif period <= 0:
                raise ValueError(period_err_msg)
            else:
                period = float(period)
        # light input checking 
        light_input_err_msg = "`light` should be a nonnegative `float`, or a callable with a single `float` parameter which returns a `float`"
        if not callable(light):
            try:
                light = float(light)
            except:
                # catches when the provided light value can't be converted to a float
                raise TypeError(light_input_err_msg)
            if light < 0:
                # catches when the provided light value is negative
                raise ValueError(light_input_err_msg)
            else:
                # create a light function that is a constant set to the provided light value
                light_fn = lambda t: light
        else:
            if len(inspect.signature(light).parameters) != 1:
                # catches when the provided light function does not take in a single parameter
                raise ValueError(light_input_err_msg)
            else: 
                try:
                    test_output = light(0.0)
                    float(test_output)
                except:
                    # catches when the function created from light does not return values that can be cast to float
                    raise ValueError(light_input_err_msg)
            # create a light function that is the provided light function
            if period != None:
                light_fn = lambda t: light(np.mod(t, period))
            else:
                light_fn = light
        # create a vectorized version of the light function that can take in numpy arrays
        self._func = np.vectorize(light_fn, otypes=[float])

    def __call__(self,
                 time: np.ndarray, # time in hours 
                 ):
        "Returns the light intensity at the provided times"
        # t type checking
        time_err_msg = "`time` should be a `float` or a 1d `numpy.ndarray` of `float`"
        try:
            time = np.array(time, dtype=float)
            if time.ndim == 0:
                try:
                    time = float(time)
                    time = np.array([time])
                except:
                    raise ValueError(time_err_msg)
            elif time.ndim != 1:
                raise ValueError(time_err_msg)
        except:
            raise ValueError(time_err_msg) 
        # calculate the light intensity at the provided times
        light_values = self._func(time)
        # throw a warning if any of the light values are negative
        if np.any(light_values < 0):
            warnings.warn("Some light values are negative")
        return light_values

    @classmethod
    def from_pulse(cls,
                   lux: float, # light intensity of the pulse in lux. Must be nonnegative
                   start: float, # start time in hours 
                   duration: float, # duration in hours. Must be positive
                   period: float = None, # period in hours, if None, then the light pulse is not repeated. Must be positive
                   baseline: float = 0.0, # baseline intensity outside of the light pulse in lux. Must be nonnegative
                   ) -> "LightSchedule":
        "Define a light schedule with a single (or a repetitive) light pulse"
        # lux input checking
        lux_err_msg = "`lux` should be a nonnegative `float` or `int`"
        if not isinstance(lux, (int, float)):
            raise TypeError(lux_err_msg)
        elif lux < 0:
            raise ValueError(lux_err_msg)
        else:
            lux = float(lux)
        # start input checking
        start_err_msg = "`start` should be a `float` or `int`"
        if not isinstance(start, (int, float)):
            raise TypeError(start_err_msg)
        else:
            start = float(start)
        # duration input checking
        duration_err_msg = "`duration` should be a positive `float` or `int`"
        if not isinstance(duration, (int, float)):
            raise TypeError(duration_err_msg)
        elif duration <= 0:
            raise ValueError(duration_err_msg)
        else:
            duration = float(duration)
        # period input checking
        period_err_msg = "`period` should be a positive `float` or `int`"
        if period != None:
            if not isinstance(period, (int, float)):
                raise TypeError(period_err_msg)
            elif period <= 0:
                raise ValueError(period_err_msg)
            else:
                period = float(period)
        # baseline input checking
        baseline_err_msg = "`baseline` should be a nonnegative `float` or `int`"
        if not isinstance(baseline, (int, float)):
            raise TypeError(baseline_err_msg)
        elif baseline < 0:
            raise ValueError(baseline_err_msg)
        else:
            baseline = float(baseline)
        # create the light schedule
        def fn(time):
            baseline_zone = (time < start) | (time > start + duration)
            light_zone = (time >= start) & (time <= start + duration)
            conditions = [baseline_zone, light_zone]
            values = [baseline, lux]
            return np.piecewise(time, conditions, values)
        return cls(fn, period=period)

# %% ../nbs/01_lights.ipynb 8
@patch_to(LightSchedule)
def __add__(self, 
            schedule: 'LightSchedule' # another LightSchedule object 
            ) -> 'LightSchedule':
    "Calculate the sum of the two LightSchedules" 
    # check that the schedule input is a LightSchedule
    schedule_err_msg = "`schedule` should be a `LightSchedule` object"
    if not isinstance(schedule, LightSchedule):
        raise TypeError(schedule_err_msg)
    fn_1 = self._func
    fn_2 = schedule._func
    lux = lambda t: fn_1(t) + fn_2(t)
    return LightSchedule(lux)

# %% ../nbs/01_lights.ipynb 10
@patch_to(LightSchedule)
def __sub__(self,
            schedule: 'LightSchedule' # another LightSchedule object
            ) -> 'LightSchedule':
    "Calculate the difference between two LightSchedules"
    # check that the schedule input is a LightSchedule
    schedule_err_msg = "`schedule` should be a `LightSchedule` object"
    if not isinstance(schedule, LightSchedule):
        raise TypeError(schedule_err_msg)
    fn_1 = self._func
    fn_2 = schedule._func
    lux = lambda t: fn_1(t) - fn_2(t)
    return LightSchedule(lux)

# %% ../nbs/01_lights.ipynb 12
@patch_to(LightSchedule)
def concatenate_at(self,
                   schedule : 'LightSchedule', # another LightSchedule object
                   timepoint: float, # timepoint (in hours) at which schedules are concatenated
                   shift_schedule: bool = True, # if True, then the schedule is shifted by the timepoint value
                   ) -> 'LightSchedule':
    "Concatenate in time two LightSchedules at the provided timepoint. Function calls for `schedule` are shifted by the timepoint value if `shift_schedule` is True. "
    # check that the schedule input is a LightSchedule
    schedule_err_msg = "`schedule` should be a `LightSchedule` object"
    if not isinstance(schedule, LightSchedule):
        raise TypeError(schedule_err_msg)
    # check that the timepoint input is a float
    timepoint_err_msg = "`timepoint` should be a `float` or `int`"
    if not isinstance(timepoint, (int, float)):
        raise TypeError(timepoint_err_msg)
    else:
        timepoint = float(timepoint)
    # check that the shift_schedule input is a bool
    shift_schedule_err_msg = "`shift_schedule` should be a `bool`"
    if not isinstance(shift_schedule, bool):
        raise TypeError(shift_schedule_err_msg)
    # create the new schedule
    fn_1 = self._func
    fn_2 = schedule._func
    def fn(t):
        func_1_zone = t < timepoint
        func_2_zone = t >= timepoint
        conditions = [func_1_zone, func_2_zone]
        if shift_schedule:
            # shift the schedule by the timepoint value
            values = [fn_1(t), fn_2(t-timepoint)]
        else:
            # don't shift the schedule
            values = [fn_1(t), fn_2(t)]
        return np.piecewise(t, conditions, values)
    return LightSchedule(fn)

# %% ../nbs/01_lights.ipynb 14
@patch_to(LightSchedule)
def plot(self, 
         plot_start_time: float, # start time of the plot in hours
         plot_end_time: float, # end time of the plot in hours
         num_samples: int=10000, # number of samples to plot
         ax=None, # matplotlib axis to plot on
         *args, # arguments to pass to matplotlib.pyplot.plot
         **kwargs # keyword arguments to pass to matplotlib.pyplot.plot
         ) -> plt.Axes:
    "Plot the light function between `start_time` and `end_time` with `num_samples` samples"
    # type checking
    if not isinstance(plot_start_time, (float, int)):
        raise ValueError(f"plot_start_time must be a float or int, got {type(plot_start_time)}")
    if not isinstance(plot_end_time, (float, int)):
        raise ValueError(f"plot_end_time must be a float or int, got {type(plot_end_time)}")
    if ax is not None:
        if not isinstance(ax, plt.Axes):
            raise ValueError(f"ax must be a matplotlib Axes object, got {type(ax)}")
    if num_samples is not None:
        if not isinstance(num_samples, int):
            raise ValueError(f"num_samples must be an int, got {type(num_samples)}")
    
    t = np.linspace(plot_start_time, plot_end_time, num_samples)
    vals = self.__call__(t)
    if ax is None:
        plt.figure()
        ax = plt.gca()

    ax.plot(t, vals, *args, **kwargs)
    return ax

# %% ../nbs/01_lights.ipynb 19
@patch_to(LightSchedule)
def RegularLight(lux: float=150.0, # intensity of the light in lux
                 lights_on: float=7.0, # time of the day for lights to come on in hours
                 lights_off: float=23.0, # time of the day for lights to go off in hours
                 ) -> 'LightSchedule':
    "Create a regular light and darkness 24 hour schedule"
    # type checking
    if not isinstance(lux, (float, int)):
        raise TypeError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(lights_on, (float, int)):
        raise TypeError(f"lights_on must be a float or int, got {type(lights_on)}")
    elif lights_on < 0.0 or lights_on > 24.0:
        raise ValueError(f"lights_on must be between 0.0 and 24.0, got {lights_on}")
    if not isinstance(lights_off, (float, int)):
        raise TypeError(f"lights_off must be a float or int, got {type(lights_off)}")
    elif lights_off < 0.0 or lights_off > 24.0:
        raise ValueError(f"lights_off must be between 0.0 and 24.0, got {lights_off}")
    
    if lights_off > lights_on:
        schedule = LightSchedule.from_pulse(lux, lights_on, lights_off - lights_on, 24.0)
        return schedule
    elif lights_off < lights_on:
        schedule = LightSchedule.from_pulse(lux, lights_on, 24.0 - lights_on, 24.0)
        schedule = schedule + LightSchedule.from_pulse(lux, 0.0, lights_off, 24.0)
        return schedule
    elif lights_off == lights_on:
        raise ValueError("lights_off and lights_on cannot be equal")

# %% ../nbs/01_lights.ipynb 21
@patch_to(LightSchedule)
def ShiftWorkLight(lux: float=150.0, # lux intensity of the light. Must be a nonnegative float or int
                   days_on: int=5, # number of days on the night shift. Must be a positive int
                   days_off: int=2, # number of days off shift. Must be a positive int
                   lights_on_workday: float=17.0, # hour of the day for lights to come on on a workday. Must be between 0.0 and 24.0
                   lights_off_workday: float=9.0, # hour of the day for lights to go off on a workday. Must be between 0.0 and 24.0
                   lights_on_day_off: float=9.0, # hour of the day for lights to come on on a day off. Must be between 0.0 and 24.0
                   lights_off_day_off: float=24.0, # hour of the day for lights to go off on a day off. Must be between 0.0 and 24.0
                   ) -> 'LightSchedule':
    "Create a light schedule for a shift worker" 
    # type checking
    lux_err_msg = "lux must be a nonnegative float or int, got "
    if not isinstance(lux, (float, int)):
        raise TypeError(lux_err_msg + f"{type(lux)}")
    elif lux < 0.0:
        raise ValueError(lux_err_msg + f"{lux}")
    days_on_err_msg = "days_on must be an int > 1, got "
    if not isinstance(days_on, int):
        raise TypeError(days_on_err_msg + f"{type(days_on)}")
    elif days_on < 2:
        raise ValueError(days_on_err_msg + f"{days_on}")
    days_off_err_msg = "days_off must be an int > 1, got "
    if not isinstance(days_off, int):
        raise TypeError(days_off_err_msg + f"{type(days_off)}")
    elif days_off < 2:
        raise ValueError(days_off_err_msg + f"{days_off}")
    lights_on_workday_err_msg = "lights_on_workday must be a float or int between 0.0 and 24.0, got "
    if not isinstance(lights_on_workday, (float, int)):
        raise TypeError(lights_on_workday_err_msg + f"{type(lights_on_workday)}")
    elif lights_on_workday < 0.0 or lights_on_workday > 24.0:
        raise ValueError(lights_on_workday_err_msg + f"{lights_on_workday}")
    lights_off_workday_err_msg = "lights_off_workday must be a float or int between 0.0 and 24.0, got "
    if not isinstance(lights_off_workday, (float, int)):
        raise TypeError(lights_off_workday_err_msg + f"{type(lights_off_workday)}")
    elif lights_off_workday < 0.0 or lights_off_workday > 24.0:
        raise ValueError(lights_off_workday_err_msg + f"{lights_off_workday}")
    lights_on_day_off_err_msg = "lights_on_day_off must be a float or int between 0.0 and 24.0, got "
    if not isinstance(lights_on_day_off, (float, int)):
        raise TypeError(lights_on_day_off_err_msg + f"{type(lights_on_day_off)}")
    elif lights_on_day_off < 0.0 or lights_on_day_off > 24.0:
        raise ValueError(lights_on_day_off_err_msg + f"{lights_on_day_off}")
    lights_off_day_off_err_msg = "lights_off_day_off must be a float or int between 0.0 and 24.0, got "
    if not isinstance(lights_off_day_off, (float, int)):
        raise TypeError(lights_off_day_off_err_msg + f"{type(lights_off_day_off)}")
    elif lights_off_day_off < 0.0 or lights_off_day_off > 24.0:
        raise ValueError(lights_off_day_off_err_msg + f"{lights_off_day_off}")
    workweek_period = 24.0 * (days_on + days_off)
    # work days regular schedule
    work_schedule = LightSchedule.RegularLight(lux, lights_on_workday, lights_off_workday)
    # transition between work days and day off - sleep half of the time between `lights_off_workday` and `lights_on_day_off`
    workdays_finish = 24*(days_on - 1) + lights_on_workday
    first_transition_end = 24*days_on + lights_on_day_off
    transition_sleep_time = 0.5 * (workdays_finish + first_transition_end) - workdays_finish
    transition_day = LightSchedule.from_pulse(lux, workdays_finish, transition_sleep_time)
    # days off regular schedule
    days_off_schedule = LightSchedule.RegularLight(lux, lights_on_day_off, lights_off_day_off)
    # transition between day off and work day - sleep, in two chunks, a third of what's left until next workday
    second_transition_start = 24*(days_on + days_off - 2) + lights_off_day_off 
    workdays_start_again = 24*(days_on + days_off - 1) + lights_on_workday
    sleep_bank = (workdays_start_again - second_transition_start) / 3.0
    transition_sleep = LightSchedule.from_pulse(lux, second_transition_start + sleep_bank, sleep_bank, workweek_period)
    # create the schedule
    total_schedule = work_schedule.concatenate_at(transition_day, workdays_finish, shift_schedule=False)
    total_schedule = total_schedule.concatenate_at(days_off_schedule, first_transition_end, shift_schedule=False)
    total_schedule = total_schedule.concatenate_at(transition_sleep, second_transition_start, shift_schedule=False)
    total_schedule = total_schedule.concatenate_at(work_schedule, workdays_start_again, shift_schedule=False)
    # add workweek periodicity
    final_schedule = LightSchedule(total_schedule, period=workweek_period)
    return final_schedule

# %% ../nbs/01_lights.ipynb 24
@patch_to(LightSchedule)
def SlamShift(lux: float=150.0, # intensity of the light in lux
              shift: float=8.0, # shift in the light schedule in hours
              before_days: int=10, # days before the shift occurs 
              starting_lights_on: float=7.0, # time of the day for lights to come on
              starting_lights_off: float=23.0, # time of the day for lights to go off
              ) -> 'LightSchedule':
    "Create a light schedule for a shift worker under a slam shift" 
    # type checking
    if not isinstance(lux, (float, int)):
        raise ValueError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(shift, (float, int)):
        raise ValueError(f"shift must be a nonnegative float or int, got {type(shift)}")
    elif shift < 0.0:
        raise ValueError(f"shift must be a nonnegative float or int, got {shift}")
    if not isinstance(before_days, int):
        raise ValueError(f"before_days must be a nonnegative int, got {type(before_days)}")
    elif before_days < 0:
        raise ValueError(f"before_days must be a nonnegative int, got {before_days}")
    if not isinstance(starting_lights_on, (float, int)):
        raise ValueError(f"starting_lights_on must be a float or int between 0 and 24, got {type(starting_lights_on)}")
    elif starting_lights_on < 0.0 or starting_lights_on > 24.0:
        raise ValueError(f"starting_lights_on must be a float or int between 0 and 24, got {starting_lights_on}")
    if not isinstance(starting_lights_off, (float, int)):
        raise ValueError(f"starting_lights_off must be a float or int between 0 and 24, got {type(starting_lights_off)}")
    elif starting_lights_off < 0.0 or starting_lights_off > 24.0:
        raise ValueError(f"starting_lights_off must be a float or int between 0 and 24, got {starting_lights_off}")
    # create the schedule
    schedule_before = LightSchedule.RegularLight(lux, starting_lights_on, starting_lights_off)
    last_lights_off_before = 24.0 * (before_days - 1) + starting_lights_off 
    first_lights_on_after =  24.0 * before_days + starting_lights_on + shift
    # sleep one third of the time between `last_lights_off_before` and `first_lights_on_after`
    transition_sleep_time =  (first_lights_on_after - last_lights_off_before) / 3.0
    transition_schedule = LightSchedule.from_pulse(lux, last_lights_off_before + transition_sleep_time, transition_sleep_time)
    shifted_lights_on = np.mod(starting_lights_on + shift, 24.0)
    shifted_lights_off = np.mod(starting_lights_off + shift, 24.0)
    schedule_after = LightSchedule.RegularLight(lux, shifted_lights_on, shifted_lights_off)
    final_schedule = schedule_before.concatenate_at(transition_schedule, last_lights_off_before, shift_schedule=False)
    final_schedule = final_schedule.concatenate_at(schedule_after, first_lights_on_after, shift_schedule=False)
    return final_schedule

# %% ../nbs/01_lights.ipynb 26
@patch_to(LightSchedule)
def SocialJetlag(lux: float=150.0, # intensity of the light in lux
                 num_regular_days: int=5, # number of days with a regular schedule
                 num_jetlag_days: int=2, # number of days with a delayed schedule
                 hours_delayed: float=2.0, # number of hours to delay the schedule on the jetlag days
                 regular_days_lights_on: float=7.0, # hour of the day for lights to come on
                 regular_days_lights_off: float=23.0, # hour of the day for lights to go off
                 ) -> 'LightSchedule':
    "Create a light schedule that simulates the effects of staying up late on the weekend (social jetlag)"
    # type checking
    if not isinstance(lux, (float, int)):
        raise TypeError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(num_regular_days, int):
        raise TypeError(f"num_regular_days must be a nonnegative int, got {type(num_regular_days)}")
    elif num_regular_days < 0:
        raise ValueError(f"num_regular_days must be a nonnegative int, got {num_regular_days}")
    if not isinstance(num_jetlag_days, int):
        raise TypeError(f"num_jetlag_days must be a nonnegative int, got {type(num_jetlag_days)}")
    elif num_jetlag_days < 0:
        raise ValueError(f"num_jetlag_days must be a nonnegative int, got {num_jetlag_days}")
    if not isinstance(hours_delayed, (float, int)):
        raise TypeError(f"hours_delayed must be a nonnegative float or int, got {type(hours_delayed)}")
    elif hours_delayed < 0.0:
        raise ValueError(f"hours_delayed must be a nonnegative float or int, got {hours_delayed}")
    if not isinstance(regular_days_lights_on, (float, int)):
        raise TypeError(f"regular_days_lights_on must be a float or int between 0 and 24, got {type(regular_days_lights_on)}")
    elif regular_days_lights_on < 0.0 or regular_days_lights_on > 24.0:
        raise ValueError(f"regular_days_lights_on must be a float or int between 0 and 24, got {regular_days_lights_on}")
    if not isinstance(regular_days_lights_off, (float, int)):
        raise TypeError(f"regular_days_lights_off must be a float or int between 0 and 24, got {type(regular_days_lights_off)}")
    elif regular_days_lights_off < 0.0 or regular_days_lights_off > 24.0:
        raise ValueError(f"regular_days_lights_off must be a float or int between 0 and 24, got {regular_days_lights_off}")
    # create the schedule 
    overall_period = 24.0 * (num_regular_days + num_jetlag_days)
    regular_days = LightSchedule.RegularLight(lux, lights_on=regular_days_lights_on, lights_off=regular_days_lights_off)
    jetlag_days = LightSchedule.RegularLight(lux, lights_on=regular_days_lights_on + hours_delayed,
                                             lights_off=np.mod(regular_days_lights_off + hours_delayed, 24))
    timepoint_change = 24.0 * (num_regular_days - 1) + regular_days_lights_off
    total_schedule = regular_days.concatenate_at(jetlag_days, timepoint_change, shift_schedule=False)
    final_schedule = LightSchedule(total_schedule, period=overall_period)
        
    return final_schedule

# %% ../nbs/01_lights.ipynb 28
# TODO: Replace the use of these two functions with LightSchedules
def make_pulse(t, tstart, tend, steep: float=30.0):
    return 0.5*np.tanh(steep*(t-tstart))-0.5*np.tanh(steep*(t-tend))

def get_pulse(t: float,
              t1: float,
              t2: float,
              repeat=False,
              Intensity: float = 150.0):

    if repeat:
        t = np.fmod(t, 24.0)
    if t < 0.0:
        t += 24.0

    light_value = Intensity*make_pulse(t, t1, t2)
    return np.abs(light_value)
