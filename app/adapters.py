import math
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

# 1. LeetCode Linked List representation
class ListNode:
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next

    def __repr__(self) -> str:
        return f"ListNode({self.val})"

def build_linked_list(values: Optional[List[Any]]) -> Optional[ListNode]:
    if not values:
        return None
    dummy = ListNode(0)
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next

def linked_list_to_list(head: Optional[ListNode], max_nodes: int = 10000) -> List[Any]:
    result = []
    visited = set()
    curr = head
    count = 0
    while curr and count < max_nodes:
        if id(curr) in visited:
            # Cycle detected
            result.append(f"[Cycle to val={curr.val}]")
            break
        visited.add(id(curr))
        result.append(curr.val)
        curr = curr.next
        count += 1
    return result

# 2. LeetCode Binary Tree representation (Level-order / BFS serialization)
class TreeNode:
    def __init__(self, val: int = 0, left: Optional["TreeNode"] = None, right: Optional["TreeNode"] = None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"TreeNode({self.val})"

def build_tree(values: Optional[List[Optional[Any]]]) -> Optional[TreeNode]:
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = [root]
    i = 1
    n = len(values)
    while queue and i < n:
        node = queue.pop(0)
        if i < n and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < n and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root

def tree_to_list(root: Optional[TreeNode]) -> List[Optional[Any]]:
    if not root:
        return []
    result: List[Optional[Any]] = []
    queue: List[Optional[TreeNode]] = [root]
    while queue:
        node = queue.pop(0)
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    # Trim trailing Nones
    while result and result[-1] is None:
        result.pop()
    return result

# 3. Base Adapter & Registry
class TypeAdapter:
    """Base class for domain-specific test adapters."""
    name: str = "base"

    def prepare_input(self, val: Any) -> Any:
        return val

    def format_output(self, val: Any) -> Any:
        return val

    def are_equal(self, actual: Any, expected: Any) -> bool:
        return deep_equal(actual, expected)

class LinkedListAdapter(TypeAdapter):
    name = "linked_list"

    def prepare_input(self, val: Any) -> Any:
        if isinstance(val, list):
            return build_linked_list(val)
        return val

    def format_output(self, val: Any) -> Any:
        if isinstance(val, ListNode):
            return linked_list_to_list(val)
        return val

    def are_equal(self, actual: Any, expected: Any) -> bool:
        act = self.format_output(actual)
        exp = self.format_output(expected) if isinstance(expected, ListNode) else expected
        return deep_equal(act, exp)

class BinaryTreeAdapter(TypeAdapter):
    name = "binary_tree"

    def prepare_input(self, val: Any) -> Any:
        if isinstance(val, list):
            return build_tree(val)
        return val

    def format_output(self, val: Any) -> Any:
        if isinstance(val, TreeNode):
            return tree_to_list(val)
        return val

    def are_equal(self, actual: Any, expected: Any) -> bool:
        act = self.format_output(actual)
        exp = self.format_output(expected) if isinstance(expected, TreeNode) else expected
        return deep_equal(act, exp)

class DesignClassAdapter(TypeAdapter):
    name = "design_class"

    def run_design_test(self, cls: Type, commands: List[str], args: List[List[Any]]) -> List[Any]:
        results: List[Any] = []
        instance = None
        for cmd, arg_list in zip(commands, args):
            if cmd == cls.__name__ or instance is None:
                instance = cls(*arg_list)
                results.append(None)
            else:
                method = getattr(instance, cmd)
                res = method(*arg_list)
                results.append(res)
        return results

class AdapterRegistry:
    """Registry for managing problem-family adapters."""
    _adapters: Dict[str, TypeAdapter] = {
        "default": TypeAdapter(),
        "linked_list": LinkedListAdapter(),
        "binary_tree": BinaryTreeAdapter(),
        "design_class": DesignClassAdapter(),
    }

    @classmethod
    def register(cls, name: str, adapter: TypeAdapter) -> None:
        cls._adapters[name] = adapter

    @classmethod
    def get(cls, name: str) -> TypeAdapter:
        return cls._adapters.get(name, cls._adapters["default"])

    @classmethod
    def detect_adapter_for_problem(cls, slug: str, category: str, class_name: str) -> TypeAdapter:
        if class_name != "Solution":
            return cls.get("design_class")
        if category == "Linked List":
            return cls.get("linked_list")
        if category in ("Trees", "Binary Search Tree"):
            return cls.get("binary_tree")
        return cls.get("default")

# 4. Universal deep comparator with float tolerance and collection normalization
def deep_equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, ListNode):
        actual = linked_list_to_list(actual)
    if isinstance(expected, ListNode):
        expected = linked_list_to_list(expected)

    if isinstance(actual, TreeNode):
        actual = tree_to_list(actual)
    if isinstance(expected, TreeNode):
        expected = tree_to_list(expected)

    if isinstance(actual, float) and isinstance(expected, (int, float)):
        return math.isclose(actual, float(expected), rel_tol=1e-5, abs_tol=1e-5)
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return math.isclose(float(actual), expected, rel_tol=1e-5, abs_tol=1e-5)

    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        if len(actual) != len(expected):
            return False
        # Direct element-wise comparison
        if all(deep_equal(a, e) for a, e in zip(actual, expected)):
            return True
        # If both are lists of lists/sets, try sorted comparison for order-independent problems (e.g., 3Sum, Group Anagrams)
        try:
            norm_actual = sorted([sorted(x) if isinstance(x, (list, tuple)) else x for x in actual], key=lambda x: str(x))
            norm_expected = sorted([sorted(x) if isinstance(x, (list, tuple)) else x for x in expected], key=lambda x: str(x))
            return all(deep_equal(a, e) for a, e in zip(norm_actual, norm_expected))
        except Exception:
            return False

    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual.keys()) != set(expected.keys()):
            return False
        return all(deep_equal(actual[k], expected[k]) for k in actual)

    return actual == expected
