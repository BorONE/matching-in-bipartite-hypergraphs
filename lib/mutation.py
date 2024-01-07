import random

from lib.trace import Trace
from lib.solution import Solution


def TryAssignRandomIdleCandidateToRandomRoute(
        solution: Solution, epoch: int, trace: Trace) -> None:
    if solution.get_idle_candidates_count() == 0:
        return

    candidate, _route = solution.get_random_idle_candidate()

    routes = list(trace.candidates[candidate])
    route = random.choice(routes)
    if solution.customer_overlap(trace.customers_by_route[route]):
        return

    solution.make_busy(candidate, route)
    return True


def AssignRandomIdleCandidateToRandomRouteIfPossible(
        solution: Solution, epoch: int, trace: Trace) -> None:
    found = False

    for candidate, route in solution.iter_candidates(busy=False, shuffle=True):
        assert route is None
        route, score = random.choice(trace.candidates_linear[candidate])
        if not solution.customer_overlap(trace.customers_by_route[route]):
            found = True
            break

    if not found:
        return

    solution.make_busy(candidate, route)
    return True


def TryRecallRandomBusyCandidate(
        solution: Solution, epoch: int, trace: Trace) -> None:
    if solution.get_busy_candidates_count() == 0:
        return

    candidate, _route = solution.get_random_busy_candidate()
    solution.make_idle(candidate)
    return True


def AssignRandomIdleCandidateToRandomRouteTillImpossible(
        solution: Solution, epoch: int, trace: Trace) -> None:
    success = True
    while success:
        success = AssignRandomIdleCandidateToRandomRouteIfPossible(solution, epoch, trace)
    return True


def MakeRoomForRandomCandidate(
        solution: Solution, epoch: int, trace: Trace) -> None:
    # TODO optimize:
    # TODO 1 better cycle
    # TODO 2 used customers know their candidates

    candidate, route = solution.get_random_candidate()
    if route is not None:
        solution.make_idle(candidate)

    room = set()
    for route in trace.candidates[candidate]:
        room |= trace.customers_by_route[route]

    # let the gods help us (TODO very bad, very good or smth in between performance)
    while solution.customer_overlap(room):
        candidate, route = solution.get_random_busy_candidate()
        if trace.customers_by_route[route] & room:
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
    def f(solution: Solution, epoch: int, trace: Trace):
        if epoch_predicat(epoch):
            return mutation_on_true(solution, epoch, trace)
        else:
            return False
    return f
