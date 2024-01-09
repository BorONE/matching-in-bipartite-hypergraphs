import typing as tp

from lib.solver.solver import Solver
from lib.anneal import anneal, anneal_beamsearch
from lib.solution import Solution
from lib.task import Task, TaskSolution
from lib.temperature import TTemperature


class AnnealSolver(Solver):
    def __init__(
        self,
        mutation: tp.Callable[[Solution, int], bool],
        epoches: int,
        temp: TTemperature,
        beamsearch_size : int | None = None,
    ) -> None:
        super().__init__()
        self.mutation = mutation
        self.epoches = epoches
        self.temp = temp
        self.beamsearch_size = beamsearch_size

    def solve(self, task: Task) -> None:
        def metric(solution: Solution) -> float:
            return -solution.get_score()

        def mutate(solution: Solution, epoch: int) -> Solution:
            solution = solution.diff()
            self.mutation(solution, epoch)
            return solution
        
        solution = Solution.empty(task.trace)
        temperature = self.temp(self.epoches)

        task_solution = TaskSolution()
        
        if self.beamsearch_size is None:
            history = anneal(solution, iter(temperature), metric, mutate)

            for _curr, f_curr in history:
                epoch_score = -f_curr
                task_solution.score_history_all.append([epoch_score])
                task_solution.score_history.append(epoch_score)
        else:
            history = anneal_beamsearch(solution, iter(temperature), metric, mutate, size=self.beamsearch_size)

            for entry in history:
                epoch_scores = [-f_curr for _curr, f_curr in entry]
                task_solution.score_history_all.append(epoch_scores)
                task_solution.score_history.append(max(epoch_scores))

        task.task_solutions.append(task_solution)
