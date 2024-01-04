import typing as tp
import numpy as np


TTemperature = tp.Callable[[int], tp.Iterator[float]]


def linear(init: float, replace_zero_with_value: float=1e-9) -> TTemperature:
    assert init > 0
    assert replace_zero_with_value > 0
    def temperature(epoches: int) -> tp.Iterable:
        temp = np.linspace(init, 0, epoches)
        temp[-1] = replace_zero_with_value
        return temp
    return temperature


def exponential(init: float, coefficient: float) -> TTemperature:
    def temperature(epoches: int) -> tp.Iterable:
        temp = np.power(coefficient, -np.arange(epoches)) * init
        return temp
    return temperature
