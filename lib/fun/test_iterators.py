from lib.fun.iterators import duplicate, take


def test_duplicate():
    assert list(duplicate(range(3))) == [0, 0, 1, 1, 2, 2]
    assert list(duplicate(range(2), n=5)) == [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    assert list(duplicate(range(1_000_000), n=0)) == []


def test_take():
    assert list(take(range(5), n=3)) == [0, 1, 2]
    assert list(take(range(3), n=5)) == [0, 1, 2]
