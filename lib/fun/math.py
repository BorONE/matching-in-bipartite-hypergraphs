import numpy as np


def softmax(x, temperature: float):
    """
    :param x:
    :param temperature: 
    
    NB
    t -> +inf => softmax -> np.arange(n) / n
    t -> 0 => softmax -> (0, .. 1, .. 0) with 1 at pos argmax()
    """
    result = np.array(x) - max(x) # hack to deal with overflow
    result = np.exp(result / temperature)
    return result / result.sum()


def softmax_for_choices(x, temperature: float):
    """
    random_choices(..., weights=softmax(x)) gives the same result as
    random_choices(..., cum_weights=softmax_for_choices(x)), but the second is faster
    """
    result = np.array(x) - max(x) # hack to deal with overflow
    result = np.exp(result / temperature)
    return np.cumsum(result)
