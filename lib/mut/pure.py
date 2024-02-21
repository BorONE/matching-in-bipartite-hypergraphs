import numpy as np
import random

from lib.mut.util import _try_make_busy_greedy, _try_make_busy_weighted_random
from lib.solution import Solution
from lib.trace import TCandidateKey, TRouteKey, TCustomerKey
from lib.fun.math import softmax_for_choices
from lib.fun.iterators import take


class MakeIdle:
    def __call__(self, solution: Solution, epoch: int) -> bool:
        if solution.get_busy_candidates_count() > 0:
            candidate, _route = solution.get_random_busy_candidate()
            solution.make_idle(candidate)
            return True
        return False


class RandomMakeBusy:
    def __init__(self, candidate_retries: int=1) -> None:
        self.candidate_retries = candidate_retries
    def __call__(self, solution: Solution, epoch: int) -> bool:   
        idle_candidates = solution.iter_candidates(busy=False, shuffle=True)
        for candidate, route in take(idle_candidates, n=self.candidate_retries):
            if _try_make_busy_weighted_random(solution, candidate):
                return True
        return False


class GreedyMakeBusy:
    def __init__(self, candidate_retries: int=1) -> None:
        self.candidate_retries = candidate_retries
    def __call__(self, solution: Solution, epoch: int) -> bool:   
        idle_candidates = solution.iter_candidates(busy=False, shuffle=True)
        for candidate, route in take(idle_candidates, n=self.candidate_retries):
            if _try_make_busy_greedy(solution, candidate):
                return True
        return False


class GreedyMakeBusyAll:
    def __call__(self, solution: Solution, epoch: int) -> bool:   
        # since make_busy ivalidates iter_candidates
        buffered_solution = solution.diff()
        for candidate, route in solution.iter_candidates(busy=False, shuffle=True):
            _try_make_busy_greedy(buffered_solution, candidate)
        buffered_solution.apply()
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
    def __init__(self, temperature: float=1) -> None:
        self.temperature = temperature

    def try_wrandom_pick(self, candidate, solution, overlap: set):
        routes_n_scores = solution.trace.candidates_linear[candidate]
        _, scores = zip(*routes_n_scores) # TODO preprocess
        cum_weights = softmax_for_choices(scores, temperature=self.temperature)
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
    

class Flip(FlipBase):
    def __init__(self, temperature: float=1, random_pick_retries: int=5) -> None:
        super().__init__(temperature)
        self.random_pick_retries = random_pick_retries

    def __call__(self, solution: Solution, epoch: int) -> bool:
        if solution.get_busy_candidates_count() == 0:
            return False

        candidate, _route = solution.get_random_busy_candidate()

        route = None
        route = route or self.try_wrandom_pick(candidate, solution, solution.customer_overlap)
        route = route or self.try_determined_pick(candidate, solution, solution.customer_overlap)
        if route is None:
            return False

        solution.make_idle(candidate)
        solution.make_busy(candidate, route)
        return True


class FlippityFlop(FlipBase):
    def __init__(self, limit: int, temperature: float=1, random_pick_retries: int=5) -> None:
        super().__init__(temperature)
        self.limit = limit
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
            route = route or self.try_wrandom_pick(candidate, solution, lambda c: c & fixed_customers)
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
