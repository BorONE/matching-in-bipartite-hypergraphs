import random

from lib.trace import Trace
from lib.solution import Solution


def TryAssignRandomIdleCandidateToRandomRoute(
        solution: Solution, epoch: int) -> bool:
    trace = solution.trace
    if solution.get_idle_candidates_count() == 0:
        return False

    candidate, _route = solution.get_random_idle_candidate()

    routes = list(trace.candidates[candidate])
    route = random.choice(routes)
    if solution.customer_overlap(trace.customers_by_route[route]):
        return

    solution.make_busy(candidate, route)
    return True


def AssignRandomIdleCandidateToRandomRouteIfPossible(
        solution: Solution, epoch: int) -> bool:
    trace = solution.trace
    found = False

    for candidate, route in solution.iter_candidates(busy=False, shuffle=True):
        assert route is None
        route, score = random.choice(trace.candidates_linear[candidate])
        if not solution.customer_overlap(trace.customers_by_route[route]):
            found = True
            break

    if not found:
        return False

    solution.make_busy(candidate, route)
    return True


def TryRecallRandomBusyCandidate(
        solution: Solution, epoch: int) -> bool:
    if solution.get_busy_candidates_count() == 0:
        return

    candidate, _route = solution.get_random_busy_candidate()
    solution.make_idle(candidate)
    return True


def AssignRandomIdleCandidateToRandomRouteTillImpossible(
        solution: Solution, epoch: int) -> bool:
    success = True
    while success:
        success = AssignRandomIdleCandidateToRandomRouteIfPossible(solution, epoch)
    return True


def MakeRoomForRandomCandidate(
        solution: Solution, epoch: int) -> bool:
    trace = solution.trace
    candidate, _route = solution.get_random_candidate()
    room = set().union(*(trace.customers_by_route[route] for route in trace.candidates[candidate]))
    room = solution.customer_overlap(room)
    for candidate in solution.get_candidates_on_customers(room):
        solution.make_idle(candidate)
    return True


# def ternary(mutation_on_true, mutation_on_false, /, *, epoch_predicat):
#     def f(solution: Solution, epoch: int, trace: Trace):
#         if epoch_predicat(epoch):
#             return mutation_on_true(solution, epoch, trace)
#         else:
#             return mutation_on_false(solution, epoch, trace)
#     return f


def conditional(mutation_on_true, /, *, epoch_predicat):
    def f(solution: Solution, epoch: int):
        if epoch_predicat(epoch):
            return mutation_on_true(solution, epoch)
        else:
            return False
    return f


def concat(*mutations, success_if='always'):
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
