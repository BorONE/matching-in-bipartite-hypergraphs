from __future__ import annotations

from dataclasses import dataclass
import random
from copy import deepcopy
import typing as tp

from lib.trace import Trace, TCandidateKey, TRouteKey, TCustomerKey
from lib.funny import DictWithRandomChoice, SequenceInterface, StackedSequences, shuffled_sequence


DEBUG = False


@dataclass
class Solution:
    idle_candidates: DictWithRandomChoice[TCandidateKey, None]
    busy_candidates: DictWithRandomChoice[TCandidateKey, TRouteKey]
    used_customers: set[TCustomerKey]
    score: float

    trace: Trace

    @staticmethod
    def empty(trace: Trace) -> Solution:
        return Solution(
            idle_candidates=DictWithRandomChoice.fromkeys(trace.candidates.keys()),
            busy_candidates=DictWithRandomChoice(),
            used_customers=set(),
            score=0,
            trace=trace,
        )

    def make_busy(self, candidate: TCandidateKey, route: TRouteKey) -> None:
        if DEBUG:
            assert len(self.customer_overlap(self.trace.customers_by_route[route])) == 0
        self.idle_candidates.remove(candidate)
        self.busy_candidates.add(candidate, route)
        self.used_customers |= self.trace.customers_by_route[route]
        self.score += self.trace.candidates[candidate][route]

    def make_idle(self, candidate: TCandidateKey) -> None:
        route = self.busy_candidates[candidate]
        self.idle_candidates.add(candidate, None)
        self.busy_candidates.remove(candidate)
        self.used_customers -= self.trace.customers_by_route[route]
        self.score -= self.trace.candidates[candidate][route]

    def get_idle_candidates_count(self) -> int:
        return len(self.idle_candidates)
    def get_random_idle_candidate(self) -> tuple[TCandidateKey, None]:
        return self.idle_candidates.get_random_item()

    def get_busy_candidates_count(self) -> int:
        return len(self.busy_candidates)
    def get_random_busy_candidate(self) -> tuple[TCandidateKey, TRouteKey]:
        return self.busy_candidates.get_random_item()

    def get_random_candidate(self) -> tuple[TCandidateKey, TRouteKey | None]:
        choice = random.choices(
            [self.get_random_idle_candidate, self.get_random_busy_candidate],
            weights=[self.get_idle_candidates_count(), self.get_busy_candidates_count()],
            k=1,
        )[0]
        return choice()

    def _get_candidates_sequence_interface(self, *, busy: bool | None=None):
        if busy is None:
            return StackedSequences(self.busy_candidates.elements, self.idle_candidates.elements)
        candidates = self.busy_candidates if busy else self.idle_candidates
        return SequenceInterface.from_sequence(candidates.elements)

    def iter_candidates(self, *, busy: bool | None=None, shuffle: bool=False):
        candidates = self._get_candidates_sequence_interface(busy=busy)
        return shuffled_sequence(candidates) if shuffle else iter(candidates)

    def customer_overlap(self, customers) -> set[TCustomerKey]:
        return self.used_customers & customers

    def get_score(self) -> float:
        return self.score
    
    def diff(self) -> SolutionDiff:
        # return deepcopy(self)
        return SolutionDiff(
            parent=self,
            idle_candidates=DictWithRandomChoice(),
            busy_candidates=DictWithRandomChoice(),
            busy_candidates_count=self.get_busy_candidates_count(),
            used_customers=set(),
            unused_customers=set(),
            score=self.score,
            trace=self.trace,
        )
    
    def get_route(self, candidate) -> TRouteKey | None:
        if candidate in self.idle_candidates:
            return None
        return self.busy_candidates[candidate]

    # DEBUG
    def dump(self):
        return "INIT", dict(
            idle_candidates=dict(self.idle_candidates.elements),
            busy_candidates=dict(self.busy_candidates.elements),
            used_customers=self.used_customers,
            score=self.get_score(),
        )

    def validate(self) -> None:
        score = 0
        used_customers = dict[TCustomerKey, TCandidateKey]
        for candidate, route in self.iter_candidates():
            if route is None:
                continue

            route_customers = self.trace.customers_by_route[route]
            overlap = used_customers.keys() & route_customers
            assert not overlap, "got overlapping customers"

            score += self.trace.candidates[candidate][route]
        assert score == self.get_score()


class SkipNoneIterator:
    def __init__(self, it: tp.Iterator[tuple[TCandidateKey, TRouteKey | None]]) -> None:
        self.it = it
    
    def __iter__(self) -> tp.Iterator[tuple[TCandidateKey, TRouteKey | None]]:
        return self

    def __next__(self) -> tuple[TCandidateKey, TRouteKey | None]:
        result = None
        while result is None:
            result = next(self.it)
        return result


@dataclass
class SolutionDiff:
    parent: Solution

    idle_candidates: DictWithRandomChoice[TCandidateKey, None]
    busy_candidates: DictWithRandomChoice[TCandidateKey, TRouteKey]
    busy_candidates_count: int
    used_customers: set[TCustomerKey]
    unused_customers: set[TCustomerKey]
    score: float

    trace: Trace

    def make_busy(self, candidate: TCandidateKey, route: TRouteKey) -> None:
        if DEBUG:
            assert len(self.customer_overlap(self.trace.customers_by_route[route])) == 0
        assert self.get_route(candidate) is None

        self.busy_candidates_count += 1

        if candidate in self.idle_candidates:
            self.idle_candidates.remove(candidate)
            if self.parent.get_route(candidate) != route:
                self.busy_candidates.add(candidate, route)
        else:
            self.busy_candidates.add(candidate, route)

        self.used_customers |= self.trace.customers_by_route[route]
        self.unused_customers -= self.trace.customers_by_route[route]
        self.score += self.trace.candidates[candidate][route]

    def make_idle(self, candidate: TCandidateKey) -> None:
        assert (route := self.get_route(candidate)) is not None

        self.busy_candidates_count -= 1

        if candidate in self.busy_candidates:
            self.busy_candidates.remove(candidate)
            if self.parent.get_route(candidate) is not None:
                self.idle_candidates.add(candidate, None)
        else:
            self.idle_candidates.add(candidate, None)

        self.unused_customers |= self.parent.customer_overlap(self.trace.customers_by_route[route])
        self.used_customers -= self.trace.customers_by_route[route]
        self.score -= self.trace.candidates[candidate][route]

    def get_idle_candidates_count(self) -> int:
        return len(self.trace.candidates) - self.busy_candidates_count

    def get_random_idle_candidate(self) -> tuple[TCandidateKey, None]:
        result = None
        while result is None:
            result = random.choice(self._get_candidates_sequence_interface(busy=False))
        return result

    def get_busy_candidates_count(self) -> int:
        return self.busy_candidates_count

    def get_random_busy_candidate(self) -> tuple[TCandidateKey, TRouteKey]:
        result = None
        while result is None:
            result = random.choice(self._get_candidates_sequence_interface(busy=True))
        return result

    def get_random_candidate(self) -> tuple[TCandidateKey, TRouteKey | None]:
        choice = random.choices(
            [self.get_random_idle_candidate, self.get_random_busy_candidate],
            weights=[self.get_idle_candidates_count(), self.get_busy_candidates_count()],
            k=1,
        )[0]
        return choice()

    def _get_candidates_sequence_interface(self, *, busy: bool | None=None):
        parent_candidates = self.parent._get_candidates_sequence_interface(busy=busy)
        
        def getitem(index):
            item = parent_candidates[index]
            if item is None:
                return None
            candidate, route = item
            if (candidate in self.idle_candidates) or (candidate in self.busy_candidates):
                return None
            return candidate, route

        if busy is None:
            return StackedSequences(
                SequenceInterface(getitem, parent_candidates.__len__),
                SequenceInterface.from_sequence(self.idle_candidates.elements),
                SequenceInterface.from_sequence(self.busy_candidates.elements),
            )
        else:
            return StackedSequences(
                SequenceInterface(getitem, parent_candidates.__len__),
                SequenceInterface.from_sequence((self.busy_candidates if busy else self.idle_candidates).elements),
            )

    def iter_candidates(self, *, busy: bool | None=None, shuffle: bool=False):
        candidates = self._get_candidates_sequence_interface(busy=busy)
        return SkipNoneIterator(shuffled_sequence(candidates) if shuffle else iter(candidates))

    def customer_overlap(self, customers) -> set[TCustomerKey]:
        return (self.parent.customer_overlap(customers) | (self.used_customers & customers)) - self.unused_customers

    def get_score(self) -> float:
        return self.score

    def get_route(self, candidate) -> TRouteKey | None:
        if candidate in self.idle_candidates:
            return None
        if candidate in self.busy_candidates:
            return self.busy_candidates[candidate]
        return self.parent.get_route(candidate)
    
    def diff(self) -> SolutionDiff:
        return SolutionDiff(
            parent=self,
            idle_candidates=DictWithRandomChoice(),
            busy_candidates=DictWithRandomChoice(),
            busy_candidates_count=self.busy_candidates_count,
            used_customers=set(),
            unused_customers=set(),
            score=self.score,
            trace=self.trace,
        )
    
    def apply(self) -> Solution:
        """
        Invalidates self. Use returned parent instead.
        Make sure self.parent has only this diff as a child.
        Be aware that self children will still point to self, even if it
        invalid. You must fix that linkage externally.
        """
        for candidate, _route in self.idle_candidates:
            self.parent.make_idle(candidate)
        for candidate, _route in self.busy_candidates:
            if self.parent.get_route(candidate) is not None:
                self.parent.make_idle(candidate)
        for candidate, route in self.busy_candidates:
            self.parent.make_busy(candidate, route)
        return self.parent

    # DEBUG
    def dump(self):
        return *self.parent.dump(), dict(
            idle_candidates=dict(self.idle_candidates.elements),
            busy_candidates=dict(self.busy_candidates.elements),
            used_customers=self.used_customers,
            unused_customers=self.unused_customers,
            score=self.score,
        )

    def validate(self) -> None:
        score = 0
        used_customers = dict[TCustomerKey, TCandidateKey]
        for candidate, route in self.iter_candidates():
            if route is None:
                continue

            route_customers = self.trace.customers_by_route[route]
            overlap = used_customers.keys() & route_customers
            assert not overlap, "got overlapping customers"

            score += self.trace.candidates[candidate][route]
        assert score == self.get_score()
