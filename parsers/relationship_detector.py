import ast
from typing import Dict, List


class RelationshipDetector(ast.NodeVisitor):
    """
    Detects HOW classes and functions relate to each other.

    Three types of relationships we care about:
    1. INHERITANCE → class Dog(Animal)  means Dog inherits Animal
    2. CALLS       → inside Dog.bark(), calling Animal.speak()
    3. (More can be added later)

    WHY THIS IS SEPARATE FROM CodeAnalyzer:
    CodeAnalyzer answers "what exists?" (list of classes/functions)
    RelationshipDetector answers "how do they connect?"
    Keeping them separate = easier to maintain and extend
    """

    def __init__(self):
        self.relationships = {
            "inheritance": [],   # parent-child class relationships
            "calls": [],         # function/method call relationships
        }
        self.current_class = None   # which class we're currently inside

    def visit_ClassDef(self, node):
        """Detect inheritance: class Dog(Animal)"""
        for base in node.bases:
            parent_name = self._get_name(base)
            if parent_name != "unknown":
                self.relationships["inheritance"].append({
                    "child": node.name,
                    "parent": parent_name,
                    "line": node.lineno,
                })

        # Track which class we're in (for call detection below)
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """
        Detect function calls.
        Example: dog.speak() → caller is current class, callee is "dog.speak"
        """
        caller = self.current_class or "global"

        if isinstance(node.func, ast.Name):
            # Simple call: speak()
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Method call: dog.speak() or self.speak()
            callee = f"{self._get_name(node.func.value)}.{node.func.attr}"
        else:
            callee = "unknown"

        # Don't log unknown or self-referencing trivial calls
        if callee != "unknown":
            self.relationships["calls"].append({
                "from": caller,
                "to": callee,
                "line": node.lineno,
            })

        self.generic_visit(node)

    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"