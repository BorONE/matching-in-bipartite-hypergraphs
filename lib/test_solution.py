import pytest
import typing as tp
from copy import deepcopy

from lib.trace import Trace
from lib.solution import Solution, SolutionDiff

def generate_trace():
    return Trace(
        candidates={
            "Sam Porter Bridges": {
                "r1": 100,
                "r2": 200,
            },
            "The Veteran Porter": {
                "r3": 1000,
                "r4": 500,
                "r5": 200,
            },
        },
        customers_by_route={
            "r1": {"A"},
            "r2": {"A", "B"},
            "r3": {"B"},
            "r4": {"B", "C"},
            "r5": {"C"},
        }
    )


def test_get_candidates_on_customers():
    trace = generate_trace()
    a = Solution.empty(trace)
    a.make_busy("Sam Porter Bridges", "r1")
    assert a.get_candidates_on_customers({"A"}) == {"Sam Porter Bridges"}
    a.make_idle("Sam Porter Bridges")
    a.make_busy("Sam Porter Bridges", "r2")
    assert a.get_candidates_on_customers({"A"}) == {"Sam Porter Bridges"}
    assert a.get_candidates_on_customers({"A", "B"}) == {"Sam Porter Bridges"}
    assert a.get_candidates_on_customers({"B"}) == {"Sam Porter Bridges"}
    a.make_busy("The Veteran Porter", "r5")
    assert a.get_candidates_on_customers({"C"}) == {"The Veteran Porter"}
    assert a.get_candidates_on_customers({"A", "C"}) == {"Sam Porter Bridges", "The Veteran Porter"}
    assert a.get_candidates_on_customers({"B"}) == {"Sam Porter Bridges"}

    a = a.diff()

    assert a.get_candidates_on_customers({"A", "B", "C"}) == {"Sam Porter Bridges", "The Veteran Porter"}
    a.make_idle("Sam Porter Bridges")
    assert a.get_candidates_on_customers({"C"}) == {"The Veteran Porter"}
    a.make_busy("Sam Porter Bridges", "r1")
    assert a.get_candidates_on_customers({"A", "C"}) == {"Sam Porter Bridges", "The Veteran Porter"}


def compare(a: Solution, b: Solution, customers: set[str]):
    assert a.get_score() == b.get_score()
    assert a.get_busy_candidates_count() == b.get_busy_candidates_count()
    assert a.get_idle_candidates_count() == b.get_idle_candidates_count()
    assert a.customer_overlap(customers) == b.customer_overlap(customers)
    for busy in [None, True, False]:
        assert dict(a.iter_candidates(busy=busy)) == dict(b.iter_candidates(busy=busy))

    # repeat 100 times to ensure all candidates are present
    assert set(a.get_random_candidate() for i in range(100)) == set(b.get_random_candidate() for i in range(100))


def valid_straight(solution: Solution) -> Solution:
    solution.make_busy("Sam Porter Bridges", "r1")
    solution.make_busy("The Veteran Porter", "r4")
    return solution


def valid_unsure(solution: Solution) -> Solution:
    solution.make_busy("Sam Porter Bridges", "r2")
    solution.make_idle("Sam Porter Bridges")
    solution.make_busy("Sam Porter Bridges", "r1")
    solution.make_busy("The Veteran Porter", "r4")
    return solution


@pytest.mark.parametrize("trace,func,customers", [
    (generate_trace(), lambda solution: solution, {"A", "B", "C"}),
    (generate_trace(), valid_straight, {"A", "B", "C"}),
    (generate_trace(), valid_unsure, {"A", "B", "C"}),
])
def test_compare_solutions(trace: Trace, func, customers: set[str]):
    a = func(Solution.empty(trace))
    b = func(Solution.empty(trace).diff())
    c = func(Solution.empty(trace).diff().diff())

    compare(a, b, customers)
    compare(a, c, customers)


def test_history():
    trace: Trace = generate_trace()
    customers: set[str] = {"A", "B", "C"}

    A = [Solution.empty(trace)]
    B = [Solution.empty(trace)]

    def append():
        A.append(deepcopy(A[-1]))
        B.append(B[-1].diff())
    
    def mutate_last(mutate):
        mutate(A[-1])
        mutate(B[-1])

    def compare_all():
        assert len(A) == len(B), 'test invariant'
        try:
            for i, (a, b) in enumerate(zip(A, B), 1):
                print(i, '/', len(A))
                compare(a, b, customers)
        except AssertionError:
            from pprint import pprint
            print('a:')
            pprint(a.dump())
            print('b:')
            pprint(b.dump())
            raise

    def mutate_1(solution):
        solution.make_busy("Sam Porter Bridges", "r1")
        solution.make_busy("The Veteran Porter", "r4")
        return solution

    def mutate_2(solution):
        solution.make_idle("The Veteran Porter")
        solution.make_busy("The Veteran Porter", "r5")
        solution.make_idle("Sam Porter Bridges")
        solution.make_busy("Sam Porter Bridges", "r2")
        return solution

    def mutate_3(solution):
        solution.make_idle("Sam Porter Bridges")
        return solution

    for i, mutate in enumerate([mutate_1, mutate_2, mutate_3, ], 1):
        print(f"mutate_{i}")
        append()
        mutate_last(mutate)
        compare_all()
