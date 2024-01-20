import random
import typing as tp
import numpy as np

from lib.solution import Solution

from lib.mut import IMutation


def conditional(
        mutation_on_true: IMutation,
        mutation_on_false: IMutation | bool=True,
        /, *,
        epoch_predicat: tp.Callable[[int], bool],
        ) -> IMutation:

    def impl(solution: Solution, epoch: int):
        if epoch_predicat(epoch):
            return mutation_on_true(solution, epoch)
        else:
            if isinstance(mutation_on_false, bool):
                return mutation_on_false
            return mutation_on_false(solution, epoch)
    return impl


def concat(
        *mutations: IMutation,
        success_if: str='always',
        ) -> IMutation:

    success_ifs = {
        'always': lambda results: True,
        'any': lambda results: any(results),
        'all': lambda results: all(results),
    }

    assert success_if in success_ifs
    success = success_ifs[success_if]

    def impl(solution, epoch) -> bool:
        return success([mutation(solution, epoch) for mutation in mutations])
    return impl


def randomize(
        *mutations: IMutation,
        weights: tp.Iterable[float] | None = None,
        k: int=1,
        )-> IMutation:

    if weights is None:
        weights = np.arange(len(mutations)) + 1
    else:
        weights = np.cumsum(np.array(weights))

    def impl(solution, epoch) -> bool:
        mutation = concat(*random.choices(mutations, cum_weights=weights, k=k))
        return mutation(solution, epoch)
    return impl
