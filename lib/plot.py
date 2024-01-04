import matplotlib.pyplot as plt
import numpy as np
import typing as tp
from math import floor, ceil

from lib.task import Task


def solve_history(
    *tasks: tp.Iterable[Task],
    exclude_init: bool=False,
    last_n: int | None=None,
    subplot_figsize: tuple=(7.5, 3),
    alpha: float=0.5
) -> None:
    tasks_count = last_n or len(tasks)
    cols, rows = 2, (tasks_count - 1) // 2 + 1
    figsize = (subplot_figsize[0] * cols, subplot_figsize[1] * rows)
    plt.figure(figsize=figsize)

    for i, task in enumerate(tasks, 1):
        plt.subplot(rows, cols, i)

        baseline = task.trace.yandex_score
        all_scores = [task_solution.score_history for task_solution in task.task_solutions]

        if last_n is not None:
            all_scores = all_scores[-last_n:]

        if exclude_init:
            all_scores = [scores[1:] for scores in all_scores]

        reach = [scores for scores in all_scores if max(scores) >= baseline]
        below = [scores for scores in all_scores if max(scores) < baseline]

        plt.grid(color='gray', linestyle=':', linewidth=1)

        # reach_frac = round(len(reach) / len(all_scores) * 100, 1)
        reach_frac = len(reach) * 100 // len(all_scores)
        below_frac = 100 - reach_frac

        if below:
            plt.plot(below[0], color='red', alpha=alpha, label=f'below baseline ({below_frac}%)')
            plt.plot(list(zip(*below[1:])), color='red', alpha=alpha)

        if reach:
            plt.plot(reach[0], color='green', alpha=alpha, label=f'baseline reached ({reach_frac}%)')
            plt.plot(list(zip(*reach[1:])), color='green', alpha=alpha)

        plt.plot([baseline] * len(all_scores[0]), label='baseline', color='blue', ls=':')
        plt.legend()

        if i % 2 == 1:
            plt.ylabel('score')
        if (i+1) // 2 == rows:
            plt.xlabel('epoches')


def _split_scores(*tasks: Task, last_n: int | None=None, rel: bool = False) -> tuple[list[float], list[list[float]]]:
    baseline_scores, ours_scores = [], []
    for task in sorted(tasks, key=lambda task: task.trace.yandex_score):
        if last_n is None:
            task_solutions = task.task_solutions
        else:
            task_solutions = task.task_solutions[-last_n:]

        if rel:
            baseline_scores.append(1)
            ours_scores.append([task_solution.get_score() / task.trace.yandex_score for task_solution in task_solutions])
        else:
            baseline_scores.append(task.trace.yandex_score)
            ours_scores.append([task_solution.get_score() for task_solution in task_solutions])

            
    return baseline_scores, ours_scores


def get_diff(target, actual, /, *, fancy=False):
    assert len(target) == len(actual)

    total_diff = sum(m - b for b, m in zip(target, actual))
    sum_baseline = sum(b for b in target)
    total_diff_rel = total_diff / sum_baseline

    if fancy:
        if total_diff > 0:
            return f'+{total_diff}', f'+{round(total_diff_rel * 100, 2)}%'
        else:
            return f'{total_diff}', f'{round(total_diff_rel * 100, 2)}%'

    return total_diff, total_diff_rel

def total_diff(
    *tasks: Task,
    last_n: int | None=None,
    ignore_many_solutions=False,
    figsize=(6.4, 4.8)
) -> None:
    baseline_scores, ours_scores = _split_scores(*tasks, last_n=last_n)

    assert ignore_many_solutions or all(len(task_scores) == 1 for task_scores in ours_scores)
    ours_scores = [task_scores[0] for task_scores in ours_scores]

    best = (max(x, y) for x, y in zip(baseline_scores, ours_scores))
    worst = (min(x, y) for x, y in zip(baseline_scores, ours_scores))

    x = range(len(baseline_scores))

    plt.figure(figsize=figsize)

    plt.grid(color='gray', linestyle=':', linewidth=1)

    plt.fill_between(x, baseline_scores, list(best), color='green', alpha=0.5, label='ours (better)')
    plt.fill_between(x, baseline_scores, list(worst), color='red', alpha=0.5, label='ours (worse)')
    plt.plot(baseline_scores, alpha=.2, color='b', label='baseline')

    plt.legend()

    _abs, rel = get_diff(baseline_scores, ours_scores, fancy=True)
    plt.title(rel)


# TODO refactor below
# or even think of smth better

T = tp.TypeVar


def _duplicate(it: tp.Iterator[T], n: int=2) -> tp.Iterator[T]:
    for elem in it:
        for i in range(n):
            yield elem


def total_diff_interval(
    *tasks: Task,
    confidence_interval: tuple[float, float] | None=None,
    last_n: int | None=None,
    rel: bool=False
) -> None:    
    baseline_scores, ours_scores = _split_scores(*tasks, last_n=last_n, rel=rel)

    # duplicate to prettify fill_between
    baseline_scores = list(_duplicate(iter(baseline_scores)))
    ours_scores = list(_duplicate(iter(ours_scores)))


    assert confidence_interval is not None, "expected confidence_interval"
    lower, upper = confidence_interval
    assert 0 <= lower < upper <= 1

    def interval(sorted_values: tp.Iterable):
        max_index = len(sorted_values) - 1
        lower_index, upper_index = ceil(max_index * lower), floor(max_index * upper)
        assert lower_index <= upper_index
        return sorted_values[lower_index], sorted_values[upper_index]

    lower, upper = zip(*(interval(sorted(task_scores)) for task_scores in ours_scores))

    upper_green, lower_green = [], []
    upper_red, lower_red = [], []
    is_green = []
    is_red = []

    for i, (b, l, u) in enumerate(zip(baseline_scores, lower, upper)):
        assert l <= u
        if b < l:
            upper_green.append(u)
            lower_green.append(l)
            upper_red.append(l)
            lower_red.append(l)
            is_green.append(True)
            is_red.append(False)
        elif l <= b <= u:
            upper_green.append(u)
            lower_green.append(b)
            upper_red.append(b)
            lower_red.append(l)
            is_green.append(True)
            is_red.append(True)
        else: # u < b
            upper_green.append(u)
            lower_green.append(u)
            upper_red.append(u)
            lower_red.append(l)
            is_green.append(False)
            is_red.append(True)

    x = range(len(baseline_scores))

    plt.figure()

    plt.grid(color='gray', linestyle=':', linewidth=1)

    plt.fill_between(x, upper_green, lower_green, color='green', alpha=0.5, label='ours (better)', where=is_green)
    plt.fill_between(x, upper_red, lower_red, color='red', alpha=0.5, label='ours (worse)', where=is_red)
    plt.plot(baseline_scores, alpha=.2, color='b', label='baseline')

    _abs, rel_lower = get_diff(baseline_scores, lower, fancy=True)
    _abs, rel_upper = get_diff(baseline_scores, upper, fancy=True)
    plt.title(f'({rel_lower}; {rel_upper})')

    plt.legend()


def total_diff_interval_bar(
    *tasks: Task,
    confidence_interval: tuple[float, float] | None=None,
    last_n: int | None=None,
    rel: bool=False
) -> None:    
    baseline_scores, ours_scores = _split_scores(*tasks, last_n=last_n, rel=rel)

    assert confidence_interval is not None, "expected confidence_interval"
    lower, upper = confidence_interval
    assert 0 <= lower < upper <= 1

    def interval(sorted_values: tp.Iterable):
        max_index = len(sorted_values) - 1
        lower_index, upper_index = ceil(max_index * lower), floor(max_index * upper)
        assert lower_index <= upper_index
        return sorted_values[lower_index], sorted_values[upper_index]

    lower, upper = zip(*(interval(sorted(task_scores)) for task_scores in ours_scores))

    upper_green, lower_green = [], []
    upper_red, lower_red = [], []
    is_green = []
    is_red = []

    for i, (b, l, u) in enumerate(zip(baseline_scores, lower, upper)):
        assert l <= u
        if b < l:
            upper_green.append(u)
            lower_green.append(l)
            upper_red.append(l)
            lower_red.append(l)
            is_green.append(True)
            is_red.append(False)
        elif l <= b <= u:
            upper_green.append(u)
            lower_green.append(b)
            upper_red.append(b)
            lower_red.append(l)
            is_green.append(True)
            is_red.append(True)
        else: # u < b
            upper_green.append(u)
            lower_green.append(u)
            upper_red.append(u)
            lower_red.append(l)
            is_green.append(False)
            is_red.append(True)

    x = range(len(tasks))

    plt.figure()

    def plot_interval(bottom, top, color, label):
        top, bottom = np.array(top), np.array(bottom)
        plt.bar(x, top - bottom, bottom=bottom, width=.2, color=color, label=label)
    plot_interval(lower_green, upper_green, color='green', label='ours (better)')
    plot_interval(lower_red, upper_red, color='red', label='ours (worse)')
    plt.plot(x, baseline_scores, alpha=.2, color='b', label='baseline')


    plt.legend()
