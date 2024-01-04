import typing as tp

from lib.solver import Solver
from lib.task import Task, TaskSolution
from lib.temperature import TTemperature


DEBUG: bool = False


def solve(
    solver: Solver,
    *tasks: Task,
    epoches: int,
    temp: TTemperature,
    retries: int = 1,
    tqdm: tp.Callable[[tp.Iterable[Task]], tp.Iterable[Task]] | None = None,
    beamsreach_size: int | None,
) -> None:
    for task in tasks if tqdm is None else tqdm(tasks):
        solver.trace = task.trace

        for _retry in range(retries):
            task_solution = TaskSolution()

            if beamsreach_size is None:
                history = solver.anneal(temp(epoches))
                
                for _curr, f_curr in history:
                    epoch_score = -f_curr
                    task_solution.score_history_all.append([epoch_score])
                    task_solution.score_history.append(epoch_score)

                last_entry = history[-1]
                best_solution, _best_score = last_entry
                task_solution.solution = best_solution
            else:
                history = solver.anneal_beamsearch(temp(epoches), size=beamsreach_size)

                for entry in history:
                    epoch_scores = [-f_curr for _curr, f_curr in entry]
                    task_solution.score_history_all.append(epoch_scores)
                    task_solution.score_history.append(max(epoch_scores))

                last_entry = history[-1]
                best_solution, _best_score = last_entry[0]
                task_solution.solution = best_solution

            if DEBUG:
                best_solution.verify()
        
            task.task_solutions.append(task_solution)
    
