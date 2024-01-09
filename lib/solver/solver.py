from lib.task import Task
from lib.fun.iterators import duplicate


class Solver:
    def solve(self, task: Task) -> None:
        raise NotImplementedError
    
    def solve_all(self, *tasks: Task, retries: int=1, tqdm=None) -> None:
        tasks = tuple(duplicate(tasks, n=retries))

        for task in tasks if tqdm is None else tqdm(tasks):
            self.solve(task)
