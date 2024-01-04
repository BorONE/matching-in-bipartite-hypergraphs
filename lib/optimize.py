def f(n):
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    assert(len(alphabet) == 26)
    if n == 0: 
        return 'A'

    result = []
    while n > 0:
        symbol = alphabet[n % len(alphabet)]
        n //= len(alphabet)
        result.append(symbol)

    return ''.join(result[::-1])


def fancy_id(obj=None, obj_id=None, cache={}):
    if obj is None and obj_id is None:
        cache.clear()
        return

    if obj_id is None:
        obj_id = id(obj)
    return cache.setdefault(obj_id, f(len(cache)))


# DEBUG
def dump_tree(tree):
    return {fancy_id(parent): [fancy_id(child) for child in children] for parent, children in tree.items()}  


def build_tree(solutions, children_as=list):
    q = solutions[:]
    tree, root = dict(), None
    while q:
        solution = q.pop()
        tree.setdefault(id(solution), dict())
        if hasattr(solution, 'parent'):
            # dict[id:solution] is used to get rid of duplicates
            tree.setdefault(id(solution.parent), dict())[id(solution)] = solution
            q.append(solution.parent)
        else:
            assert root is None or root is solution, f"found multiple solutions with not parent: {root.dump()}, {solution.dump()}"
            root = solution
    assert root is not None

    for parent, children in tree.items():
        tree[parent] = children_as(children.values())

    return tree, root


def optimize_tree(tree, root):
    result = []
    layer = [root]
    while layer:
        next_layer = []
        for parent in layer:
            children = tree[id(parent)]

            if len(children) == 0:
                result.append(parent)

            elif len(children) == 1:
                child = children.pop()
                assert child.apply() == parent
             
                grandchildren = tree.get(id(child), [])
                for grandchild in grandchildren:
                    grandchild.parent = parent
                tree[id(parent)] = grandchildren
                next_layer.append(parent)

            else:
                next_layer.extend(children)

        layer = next_layer
    return result


def optimize(solutions):
    """
    Collapse nodes, with single child, e.g.

              +->F
              |
        A->B->C->D->E

    will be collapsed to 

        +->F
        |
        ABC->DE

    and

        A->B->C->D->E

    will be collapsed to

        ABCDE

    WHY
    SolutionDiffs can be represented as a tree of patches. In a not beamsearch
    anneal we can collapse all patches since there will be no conflicts. But in
    the case of beamsearch we have not just single solution. Such solutions
    will have common history at some point and we cannot callapse such trees,
    because it will invalidate other solutions.

    BRIEF ALGO EXPLANATION
    - Build a tree. Will be done new-to-old, since we have access only to 
        newest solutions. 
    - Iterate old-to-new, and in case of single child, collapse child into
        current node. Make sure not to invalidate connections both in our
        (old-to-new) tree and solutions' parent linkage.
    """

    root: int | None = None
    tree = dict() #: dict[id(solution), soluton.children: list[Solution]]
    tree, root = build_tree([solution for solution, _score in solutions])

    result = optimize_tree(tree, root)

    # we can calculate score fast enough
    return [(solution, -solution.get_score()) for solution in result]
