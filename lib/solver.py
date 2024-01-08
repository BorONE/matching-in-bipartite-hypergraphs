import random

from lib.anneal import anneal, anneal_beamsearch
from lib.trace import Trace
from lib.solution import Solution

from copy import copy


class MutationLike:
    def __call__(self, solution: Solution, epoch: int) -> bool:
        pass


class Solver:
    def __init__(
        self,
        *,
        mutation: MutationLike,
    ) -> None:
        self.trace = None
        self.mutation = mutation

    def _metric(self, solution: Solution) -> float:
        return -solution.get_score()

    def _mutate(self, solution: Solution, epoch: int) -> Solution:
        solution = solution.diff()
        self.mutation(solution, epoch)
        return solution

    def anneal(self, temp_it):
        return anneal(Solution.empty(self.trace), temp_it, self._metric, self._mutate)

    def anneal_beamsearch(self, temp_it, size=2):
        return anneal_beamsearch(Solution.empty(self.trace), temp_it, self._metric, self._mutate, size)
