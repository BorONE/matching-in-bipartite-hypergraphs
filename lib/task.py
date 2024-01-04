import pandas as pd
import typing as tp
from dataclasses import dataclass, field

from lib.trace import Trace, from_df as trace_from_df
from lib.solution import Solution

@dataclass
class TaskSolution:
    """
    In case of beamsearch
    - score_history contains *best* soluions at each epoch
    - score_history_all contains *all* soluions at each epoch
    else not used yet
    """

    score_history: list[float] = field(default_factory=list)
    score_history_all: list[float] = field(default_factory=list)
    solution: Solution | None = None # TODO don't invalidate best solution while optimizing (see optimize.py)

    def get_score(self) -> float:
        assert len(self.score_history) > 0
        return max(self.score_history)


@dataclass
class Task:
    trace: Trace
    task_solutions: list[TaskSolution] = field(default_factory=list)


def make_tasks(data: tp.Iterable[dict[str, pd.DataFrame]]):
    return [Task(trace_from_df(df['trace'], df['routes'])) for df in data]   
