import random

from lib.anneal import anneal, anneal_beamsearch
from lib.trace import Trace
from lib.solution import Solution

from copy import copy


class MutationLike:
    def __call__(self, solution: Solution, epoch: int, trace: Trace) -> bool:
        pass


class Solver:
    def __init__(
        self,
        trace: Trace,
        mutations: list[MutationLike],
        strategy: str = 'one_shot'
    ) -> None:
        self.trace = trace
        self.mutations = mutations
        self.strategy = strategy

        # verify correct strategy
        getattr(self, f"_mutate_{self.strategy}")

    def metric(self, solution: Solution) -> float:
        return -solution.get_score()

    def mutate(self, solution: Solution, epoch: int) -> Solution:
        return getattr(self, f"_mutate_{self.strategy}")(solution, epoch)

    def _mutate_one_shot(self, solution: Solution, epoch: int) -> Solution:
        mutation = random.choice(self.mutations)
        solution = solution.diff()
        mutation(solution, epoch, trace=self.trace)
        return solution

    def _mutate_till_success(self, solution: Solution, epoch: int) -> Solution:
        solution = solution.diff()
        while True:
            mutation = random.choice(self.mutations)
            if mutation(solution, epoch, trace=self.trace):
                return solution

    def _mutate_all(self, solution: Solution, epoch: int) -> Solution:
        solution = solution.diff()
        mutations = copy(self.mutations)
        # random.shuffle(mutations)
        for mutation in mutations:
            mutation(solution, epoch, trace=self.trace)
        return solution

    def anneal(self, temp_it):
        return anneal(Solution.empty(self.trace), temp_it, self.metric, self.mutate)

    def anneal_beamsearch(self, temp_it, size=2):
        return anneal_beamsearch(Solution.empty(self.trace), temp_it, self.metric, self.mutate, size)
