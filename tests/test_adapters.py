from app.adapters import (
    AdapterRegistry,
    BinaryTreeAdapter,
    DesignClassAdapter,
    LinkedListAdapter,
    ListNode,
    TreeNode,
    build_linked_list,
    build_tree,
    deep_equal,
    linked_list_to_list,
    tree_to_list,
)

def test_linked_list_adapter():
    """Test ListNode creation and serialization."""
    values = [1, 2, 3, 4, 5]
    head = build_linked_list(values)
    assert head.val == 1
    assert head.next.val == 2
    converted = linked_list_to_list(head)
    assert converted == values

    # Empty list
    assert build_linked_list([]) is None
    assert linked_list_to_list(None) == []

def test_linked_list_cycle_detection():
    """Test cycle detection stops infinite loops."""
    n1 = ListNode(1)
    n2 = ListNode(2)
    n3 = ListNode(3)
    n1.next = n2
    n2.next = n3
    n3.next = n1  # Cycle back to n1

    out = linked_list_to_list(n1)
    assert len(out) == 4
    assert "[Cycle to val=1]" in out[-1]

def test_tree_adapter():
    """Test TreeNode building and level-order serialization."""
    values = [3, 9, 20, None, None, 15, 7]
    root = build_tree(values)
    assert root.val == 3
    assert root.left.val == 9
    assert root.right.val == 20
    assert root.right.left.val == 15
    assert root.right.right.val == 7

    out = tree_to_list(root)
    assert out == values

def test_design_class_adapter():
    """Test command and argument execution for design classes."""
    class DummyStack:
        def __init__(self, init_val=0):
            self.stack = [init_val] if init_val else []
        def push(self, val):
            self.stack.append(val)
        def pop(self):
            return self.stack.pop() if self.stack else None
        def top(self):
            return self.stack[-1] if self.stack else None

    adapter = DesignClassAdapter()
    commands = ["DummyStack", "push", "push", "top", "pop"]
    arguments = [[10], [20], [30], [], []]
    results = adapter.run_design_test(DummyStack, commands, arguments)
    assert results == [None, None, None, 30, 30]

def test_deep_equal_comparator():
    """Test comparator with exact types, floats with tolerance, and order-independence."""
    assert deep_equal(1, 1)
    assert deep_equal(0.1 + 0.2, 0.3)
    assert deep_equal([1, 2, 3], [1, 2, 3])
    assert not deep_equal([1, 2], [1, 2, 3])

    # Order-independent nested lists (e.g., 3Sum results)
    actual_3sum = [[-1, 0, 1], [-1, -1, 2]]
    expected_3sum = [[-1, -1, 2], [-1, 0, 1]]
    assert deep_equal(actual_3sum, expected_3sum)

def test_adapter_registry_detection():
    """Test automatic detection of adapters based on problem category."""
    ll_adapter = AdapterRegistry.detect_adapter_for_problem("reverse-linked-list", "Linked List", "Solution")
    assert isinstance(ll_adapter, LinkedListAdapter)

    tree_adapter = AdapterRegistry.detect_adapter_for_problem("invert-binary-tree", "Trees", "Solution")
    assert isinstance(tree_adapter, BinaryTreeAdapter)

    design_adapter = AdapterRegistry.detect_adapter_for_problem("min-stack", "Stack", "MinStack")
    assert isinstance(design_adapter, DesignClassAdapter)
