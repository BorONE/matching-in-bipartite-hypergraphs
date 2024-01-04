from lib.funny import SequenceInterface, StackedSequences, shuffled_range, shuffled_sequence

def test_SequenceInterface_simple():
    seq = [1, 2, 3]
    si = SequenceInterface(seq.__getitem__, seq.__len__)

    assert len(si) == len(seq)
    for i in range(len(si)):
        assert si[i] == seq[i]

def test_SequenceInterface_from_sequnece():
    seq = [1, 2, 3]
    si = SequenceInterface.from_sequence(seq)

    assert len(si) == 3
    for i in range(len(si)):
        assert si[i] == seq[i]

def test_SequenceInterface_iter():
    seq = [1, 2, 3]
    si = SequenceInterface.from_sequence(seq)

    assert list(si) == seq        


#


def test_StackedSequences_simple():
    stack = StackedSequences(['a', 'aa'], [], ['b', 'bb', 'bbb'], ['c'], [])
    assert len(stack) == 6
    assert stack[0] == 'a'
    assert stack[3] == 'bb'
    assert stack[-1] == 'c'
    assert list(stack) == ['a', 'aa', 'b', 'bb', 'bbb', 'c']


def test_StackedSequences_empty():
    assert len(StackedSequences()) == 0
    assert len(StackedSequences([], [], StackedSequences([]))) == 0


def test_StackedSequences_almost_empty():
    assert list(StackedSequences([], [], [1], [], [])) == [1]


def test_StackedSequences_nested():
    stack = StackedSequences(
        StackedSequences(['a', 'aa']),
        StackedSequences(
            ['b', 'bb', 'bbb'],
            StackedSequences(StackedSequences(['c'])),
        )
    )

    assert stack[0] == 'a'
    assert stack[3] == 'bb'
    assert stack[-1] == 'c'
    assert list(stack) == ['a', 'aa', 'b', 'bb', 'bbb', 'c']

#


def test_shuffled_range():
    for i in range(1000):
        for n in range(10):
            assert sorted(shuffled_range(n)) == list(range(n))

    n = 100
    assert list(shuffled_range(n)) != list(shuffled_range(n))
    assert list(shuffled_range(n)) != list(range(n))


def test_shuffled_sequence():
    sorted_seq = ['a'] * 50 + ['b'] * 50

    shuffled_seq = shuffled_sequence(sorted_seq)
    assert sorted(shuffled_seq) == sorted_seq
    
    enumerated_shuffled_seq = shuffled_sequence(sorted_seq, enumerate=True)
    assert sorted(enumerated_shuffled_seq) == list(enumerate(sorted_seq))
    assert sorted(enumerated_shuffled_seq) != enumerate(list(sorted_seq))
    
    assert list(shuffled_sequence(sorted_seq)) != sorted_seq
    assert list(shuffled_sequence(sorted_seq)) != list(shuffled_sequence(sorted_seq))
