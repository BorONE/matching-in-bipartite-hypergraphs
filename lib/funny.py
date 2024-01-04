from __future__ import annotations

import random
from itertools import chain

import typing as tp
from collections.abc import Sequence


TKey = tp.TypeVar('TKey')
TValue = tp.TypeVar('TValue')
TIndex = int


class DictWithRandomChoice(tp.Generic[TKey, TValue]):
    """
    As the name suggests the class behaves similar to python's dict, but
    allows to get random item in constant time O(1). `__setitem__` is not
    implemented, since for our goals it is cruicial not to overwrite presence
    or absence of keys.
    """

    def __init__(self, items=()):
        self.elements: list[tuple[TKey, TValue]] = []
        self.index_map: dict[TKey, TIndex] = {}

        for key, value in items:
            self.add(key, value)

    @staticmethod
    def fromkeys(keys) -> DictWithRandomChoice:
        return DictWithRandomChoice((key, None) for key in keys)
    
    def add(self, key: TKey, value: TValue) -> None:
        assert key not in self.index_map, f"key {key} is already present in {set(self.index_map.keys())}"
        self.index_map[key] = len(self.elements)
        self.elements.append((key, value))

    def remove(self, key: TKey) -> None:
        assert key in self.index_map, f"key {key} is not present in {set(self.index_map.keys())}"
        index = self.index_map.pop(key)
        last_element = self.elements.pop()

        if index < len(self.elements):
            last_key, _last_value = last_element
            self.elements[index] = last_element
            self.index_map[last_key] = index

    def get_random_item(self) -> tuple[TKey, TValue]:
        # TODO make sure removing this if-statement is safe, remove
        if len(self) == 0:
            return None
        return random.choice(self.elements)
    
    def __getitem__(self, key: TKey) -> TValue:
        index = self.index_map[key]
        key, value = self.elements[index]
        return value

    def __iter__(self) -> tp.Iterator[tuple[TKey, TValue]]:
        return iter(self.elements)

    def __len__(self) -> int:
        return len(self.elements)
    
    def __contains__(self, key: TKey) -> bool:
        return key in self.index_map


# TODO better typing
class SequenceInterface:
    """
    Provides view interface from __getitem__, __len__ with minimal overhead
    """

    def __init__(self, getitem, len) -> None:
        self.getitem = getitem
        self.len = len
    
    @staticmethod
    def from_sequence(sequence) -> SequenceInterface:
        return SequenceInterface(sequence.__getitem__, sequence.__len__)

    def __getitem__(self, index):
        return self.getitem(index)

    def __len__(self) -> int:
        return self.len()

    def __iter__(self) -> tp.Iterator:
        return SequenceInterfaceIterator(self)


# TODO better typing
class SequenceInterfaceIterator:
    def __init__(self, seq: SequenceInterface) -> None:
        self.seq = seq
        self.iter = iter(range(len(seq)))
    
    def __iter__(self) -> SequenceInterfaceIterator:
        return self
    
    def __next__(self) -> tp.Any:
        index = next(self.iter)
        return self.seq[index]


VERSION = 0


# TODO better typing
class StackedSequences:
    """
    Provides view interface for stack of sequences with minimal overhead
    """

    def __init__(self, *seqs):
        if VERSION == 0:
            self.seqs = seqs
        if VERSION == 1:
            self.seqs = []
            for seq in seqs:
                if isinstance(seq, StackedSequences):
                    self.seqs.extend(subseq for subseq in seq.seqs)
                else:
                    self.seqs.append(seq)
        cumlen = 0
        self.cumlens = [(0, cumlen)]
        for i, seq in enumerate(self.seqs, 1):
            cumlen += len(seq)
            self.cumlens.append((i, cumlen))
        

    @staticmethod
    def from_interfaces(*interfaces):
        return StackedSequences(*(SequenceInterface(*interface) for interface in interfaces))

    def __getitem__(self, index: int):
        # Can be done with binsearch for bigger stacks, but for our purposes
        # such optimization is unnecessary, since it is not intended usage.
        if index < 0:
            index += len(self)
        assert 0 <= index < len(self), f"got index {index} for cumlen: {self.cumlens}"

        for seq_index, cumlen in self.cumlens[::-1]:
            if index >= cumlen:
                seq = self.seqs[seq_index]
                return seq[index - cumlen]

    def __len__(self) -> int:
        _, total_len = self.cumlens[-1]
        return total_len

    def __iter__(self) -> tp.Iterator:
        return chain(*(iter(seq) for seq in self.seqs))


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


class ShuffledRangeIterator:
    def __init__(self, start: int, step: int, n: int) -> None:
        assert 0 < step < n and gcd(step, n) == 1
        assert 0 <= start < n
        assert n > 1, f'use range({n})'

        self.start = start
        self.step = step
        self.n = n

        self.iter = iter(range(n))

    def __iter__(self) -> ShuffledRangeIterator:
        return self

    def __next__(self) -> int:
        index = next(self.iter)
        return (self.start + self.step * index) % self.n


def shuffled_range(n: int) -> tp.Iterable:
    """
    Just like range(n), but shuffled. Not real random, or not even honest
    permutation random, but something alike.
    """
    assert n >= 0

    if n <= 1:
        return iter(range(n))

    start = random.randrange(0, n)
    step = random.randrange(1, n)
    while (gcd_ := gcd(step, n)) != 1:
        step //= gcd_
    return ShuffledRangeIterator(start, step, n)


class ShuffledSequenceIterator:
    def __init__(self, seq: Sequence, enumerate: bool) -> None:
        self.seq = seq
        self.enumerate = enumerate

        self.iter = shuffled_range(len(seq))

    def __iter__(self) -> ShuffledSequenceIterator:
        return self

    def __next__(self):
        index = next(self.iter)
        return (index, self.seq[index]) if self.enumerate else self.seq[index]


def shuffled_sequence(seq: Sequence, enumerate=False) -> tp.Iterator:
    return ShuffledSequenceIterator(seq, enumerate=enumerate)
