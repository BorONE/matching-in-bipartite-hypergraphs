import numpy as np
import random

from lib.mut.util import _try_make_busy, _try_make_busy_greedy
from lib.solution import Solution
from lib.trace import TCandidateKey, TRouteKey, TCustomerKey


def TryMakeBusyRandomCandidateWithRandomRoute(
        solution: Solution, epoch: int) -> bool:
    
    if solution.get_idle_candidates_count() == 0:
        return False

    candidate, _route = solution.get_random_idle_candidate()
    route, _score = random.choices(solution.trace.candidates_linear[candidate], weights=solution.trace.sorted_scores[candidate])[0]
    return _try_make_busy(solution, candidate, route)


def TryMakeBusyRandomCandidateWithGreedyRoute(
        solution: Solution, epoch: int) -> bool:

    if solution.get_idle_candidates_count() == 0:
        return False

    candidate, _route = solution.get_random_idle_candidate()
    return _try_make_busy_greedy(solution, candidate)


def TryMakeIdleRandomCandidate(
        solution: Solution, epoch: int) -> bool:
    
    if solution.get_busy_candidates_count() == 0:
        return

    candidate, _route = solution.get_random_busy_candidate()
    solution.make_idle(candidate)
    return True


def TryMakeBusyAnyCandidateWithGreedyRoute(
        solution: Solution, epoch: int) -> bool:
    
    for candidate, route in solution.iter_candidates(busy=False, shuffle=True):
        if _try_make_busy_greedy(solution, candidate):
            return True
    return False

def TryMakeBusyAllCandidateWithGreedyRoute(
        solution: Solution, epoch: int) -> bool:

    # since make_busy ivalidates iter_candidates
    cached_solution = solution.diff()
    for candidate, route in list(solution.iter_candidates(busy=False, shuffle=True)):
        _try_make_busy_greedy(cached_solution, candidate)
    cached_solution.apply()
    return True


def MakeRoomForRandomCandidate(
        solution: Solution, epoch: int) -> bool:
    
    candidate, _route = solution.get_random_candidate()
    room = set().union(*(solution.trace.customers_by_route[route] for route in solution.trace.candidates[candidate]))
    room = solution.customer_overlap(room)
    for candidate in solution.get_candidates_on_customers(room):
        solution.make_idle(candidate)
    return True



class FlipBase:
    def try_random_pick(self, candidate, solution, overlap: set):
        routes_n_scores = solution.trace.candidates_linear[candidate]
        _, scores = zip(*routes_n_scores) # TODO preprocess
        cum_weights = self.softmax(scores, for_choices=True)
        for retry in range(self.random_pick_retries):
            route, score = random.choices(routes_n_scores, cum_weights=cum_weights, k=1)[0]
            if not overlap(solution.trace.customers_by_route[route]):
                return route
        return None

    def try_determined_pick(self, candidate, solution, overlap: set):
        routes_n_scores = solution.trace.candidates_linear[candidate]
        for route, score in sorted(routes_n_scores, key=lambda rns: rns[1], reverse=True):
            if not overlap(solution.trace.customers_by_route[route]):
                return route
        return None

    def softmax(self, x, for_choices=False):
        """
        :param x:
        :param temperature:
        
        note that:
            t -> +inf => softmax -> np.arange(n) / n
            t -> 0 => softmax -> (0, .. 1, .. 0) with 1 at pos argmax()
        """
        result = np.array(x) - max(x) # hack to deal with overflow
        result = np.exp(result / self.temperature)
        if for_choices:
            return np.cumsum(result)
        return result / result.sum()
    

class Flip(FlipBase):
    def __init__(self, temperature: float=1, random_pick_retries: int=5) -> None:
        self.temperature = temperature
        self.random_pick_retries = random_pick_retries

    def __call__(self, solution: Solution, epoch: int) -> bool:
        if solution.get_busy_candidates_count() == 0:
            return False

        candidate, _route = solution.get_random_busy_candidate()

        route = None
        route = route or self.try_random_pick(candidate, solution, solution.customer_overlap)
        route = route or self.try_determined_pick(candidate, solution, solution.customer_overlap)
        if route is None:
            return False

        solution.make_idle(candidate)
        solution.make_busy(candidate, route)
        return True


class FlippityFlop(FlipBase):
    def __init__(self, limit: int, temperature: float=1, random_pick_retries: int=5) -> None:
        self.limit = limit
        self.temperature = temperature
        self.random_pick_retries = random_pick_retries
    
    def __call__(self, solution: Solution, epoch: int) -> bool:
        fixed_customers = set()
        candidate, route = solution.get_random_candidate()
        if route is not None:
            solution.make_idle(candidate)
        q = [candidate]

        for i in range(self.limit):
            if i >= len(q):
                break # all conflicts are resolved

            candidate = q[i]
            assert candidate not in q[:i]

            route = None
            route = route or self.try_random_pick(candidate, solution, lambda c: c & fixed_customers)
            route = route or self.try_determined_pick(candidate, solution, lambda c: c & fixed_customers)
            if route is None:
                continue

            room = solution.trace.customers_by_route[route]
            room = solution.customer_overlap(room)
            for busy_candidate in solution.get_candidates_on_customers(room):
                solution.make_idle(busy_candidate)
                q.append(busy_candidate)
            solution.make_busy(candidate, route)
            fixed_customers |= solution.trace.customers_by_route[route]
