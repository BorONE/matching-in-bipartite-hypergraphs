from lib.solution import Solution
from lib.trace import TCandidateKey, TRouteKey, TCustomerKey


def _try_make_busy(solution: Solution, candidate: TCandidateKey, route: TRouteKey) -> bool:
    route_customers = solution.trace.customers_by_route[route]
    if not solution.customer_overlap(route_customers):
        solution.make_busy(candidate, route)
        return True
    return False

def _try_make_busy_greedy(solution: Solution, candidate: TCandidateKey) -> bool:
    for route, score in solution.trace.candidates_linear[candidate]:
        if _try_make_busy(solution, candidate, route):
            return True
    return False

