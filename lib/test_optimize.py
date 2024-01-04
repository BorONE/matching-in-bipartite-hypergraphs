from __future__ import annotations

from dataclasses import dataclass

from lib.optimize import optimize, optimize_tree, build_tree, fancy_id


class Root:
    def __init__(self) -> None:
        self.value = fancy_id(self)

    def __repr__(self) -> str:
        return self.value


class Node:
    def __init__(self, parent: Node | Root) -> None:
        self.parent = parent
        self.value = fancy_id(self)

    def apply(self) -> Node | Root:
        self.parent.value += self.value
        self.value = 'invalid'
        return self.parent

    def __repr__(self) -> str:
        return f'{self.value}({self.parent.value})'


def fancify(tree):
    return dict((fancy_id(obj_id=key), values) for key, values in tree.items())


def generate_branch_data():
    fancy_id()
    root = Root()
    node_1 = Node(parent=root)
    node_2 = Node(parent=node_1)
    node_3 = Node(parent=node_2)
    leaf_4 = Node(parent=node_3)

    leaf_3 = Node(parent=node_2)

    tree = {
        id(root)   : {node_1},
        id(node_1) : {node_2},
        id(node_2) : {node_3, leaf_3},
        id(node_3) : {leaf_4},
        id(leaf_4) : set(),
        id(leaf_3) : set(),
    }

    bamboo = {
        id(root)   : {node_1},
        id(node_1) : {node_2},
        id(node_2) : {node_3},
        id(node_3) : {leaf_4},
        id(leaf_4) : set(),
    }

    return dict(
        tree=tree,
        tree_leafs = [leaf_3, leaf_4],
        bamboo=bamboo,
        bamboo_leafs = [leaf_4],
        root=root,
        optimized_nodes = {root, node_3, leaf_3}
    )


def test_build_tree():
    data = generate_branch_data()

    assert build_tree(data['tree_leafs'], children_as=set) == (data['tree'], data['root'])
    assert build_tree(data['bamboo_leafs'], children_as=set) == (data['bamboo'], data['root'])


def test_optimize_tree():
    data = generate_branch_data()

    leafs = optimize_tree(data['tree'], data['root'])
    tree, root = build_tree(leafs)
    
    assert root is data['root']

    tree_nodes = set()
    for key, values in tree.items():
        tree_nodes.add(key)

    assert set(tree.keys()) == {id(node) for node in data['optimized_nodes']}

    assert root.value == 'ABC'

    children = tree[id(root)]
    assert len(children) == 2

    node_1, node_2 = children
    assert sorted([node_1.value, node_2.value]) == ["DE", "F"]

    assert len(tree[id(node_1)]) == 0
    assert len(tree[id(node_2)]) == 0


def test_optimize_bamboo():
    data = generate_branch_data()

    leafs = optimize_tree(data['bamboo'], data['root'])
    bamboo, root = build_tree(leafs)
    assert bamboo == {id(root) : []}
    assert root.value == "ABCDE"
