import numpy as np
import scipy.stats as sps
import typing as tp

from lib.optimize import optimize

X = tp.TypeVar('X')


class Neighbour(tp.Protocol[X]):
    @tp.overload
    def __call__(self, x: X, epoch: int) -> X:
        pass

    @tp.overload
    def __call__(self, x: X) -> X:
        pass


class Metric(tp.Protocol[X]):
    def __call__(self, x: X) -> float:
        pass


def evaluate_probability(f_curr: float, f_next: float, temp: float) -> float:
    assert temp > 0
    return np.exp(min(-(f_next - f_curr) / temp, 0))


def iterate_anneal(curr: X, f_curr: float, temp: float, f: Metric[X], A: Neighbour[X]):
    """
    :param curr: current iteration element: X
    :param curr_f: metric on current iteration element: float
    :param temp: float > 0
    :param f: metric to minimize: X -> float
    :param A: operator: X -> X
    :return: next iteration element
    """
    next = A(curr)
    f_next = f(next)

    prob = evaluate_probability(f_curr, f_next, temp)
    take_next = sps.bernoulli(prob).rvs() == 1
    return (next, f_next) if take_next else (curr, f_curr)


def anneal(init: X, temp_it: tp.Iterator[float], f: Metric[X], A: Neighbour[X]) -> X:
    """
    :param init: initial iteration element: X
    :param temp_it: iterator over temperatures, Iterator[float > 0]
    :param f: metric to minimize: X -> float
    :param A: operator: X -> X
    :return: history of pairs (x, f(x))
    """
    curr, f_curr = init, f(init)
    history = [(curr, f_curr)]
    for epoch, temp in enumerate(temp_it):
        curr, f_curr = iterate_anneal(curr, f_curr, temp, f, lambda x: A(x, epoch))

        single = optimize([(curr, f_curr)])
        assert len(single) == 1
        curr, f_curr = single[0]
        
        history.append((curr, f_curr))
    return history


def keep_best(currs: list, n: int) -> list:
    result = []
    present_result_ids = set()

    for curr, f_curr in sorted(currs, key=lambda x: x[1]):
        if id(curr) in present_result_ids:
            continue

        result.append((curr, f_curr))
        present_result_ids.add(id(curr))

        if len(result) == n:
            break
    return result


def anneal_beamsearch(init: X, temp_it: tp.Iterator[float], f: Metric[X], A: Neighbour[X], size: int=2) -> X:
    """
    :param init: initial iteration element: X
    :param temp_it: iterator over temperatures, Iterator[float > 0]
    :param f: metric to minimize: X -> float
    :param A: operator: X -> X
    :param size: size of beam search
    :return: history of [(x, f(x))] * size
    """
    currs = [(init, f(init)) for i in range(size)]
    history = [currs]
    for epoch, temp in enumerate(temp_it):
        nexts = []
        for curr, f_curr in currs:
            nexts += [iterate_anneal(curr, f_curr, temp, f, lambda x: A(x, epoch))
                      for i in range(size)]
        
        currs = keep_best(nexts, n=size)
        currs = optimize(currs)
        history.append(currs)
    return history
