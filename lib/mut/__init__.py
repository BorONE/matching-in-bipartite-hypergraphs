from lib.solution import Solution


class IMutation:
    def __call__(self, solution: Solution, epoch: int) -> bool:
        pass


from lib.mut.pure import *
from lib.mut.combine import *
