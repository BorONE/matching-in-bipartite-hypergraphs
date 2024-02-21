import typing as tp

T = tp.TypeVar('T')


def duplicate(it: tp.Iterator[T], n: int=2) -> tp.Iterator[T]:
    for elem in it:
        for i in range(n):
            yield elem


def take(it: tp.Iterable[T], n: int) -> tp.Iterable[T]:
    for _, value in zip(range(n), it):
        yield value
