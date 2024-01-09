import typing as tp

T = tp.TypeVar


def duplicate(it: tp.Iterator[T], n: int=2) -> tp.Iterator[T]:
    for elem in it:
        for i in range(n):
            yield elem

