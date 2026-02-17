import ast
from typing import List, Dict


class CodeAnalyzer(ast.NodeVisitor):
    """
    Walks through Python code's AST and extracts
    classes, functions, and imports.

    HOW AST WORKS:
    Python converts code like:
        class Dog(Animal):
            def bark(self): pass

    Into a TREE:
        Module
        └── ClassDef (name="Dog", bases=["Animal"])
            └── FunctionDef (name="bark")

    Each visit_XXX method is auto-called when that node is found.
    """

    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []
        self.in_class = False  # tracks if we're inside a class

    def visit_ClassDef(self, node):
        """Called every time AST finds a class definition"""
        class_info = {
            "name": node.name,
            "methods": [
                m.name for m in node.body
                if isinstance(m, ast.FunctionDef)
            ],
            "bases": [self._get_name(b) for b in node.bases],
            "line": node.lineno,
        }
        self.classes.append(class_info)

        # Mark that we're inside a class so visit_FunctionDef
        # knows NOT to treat methods as top level functions
        old_in_class = self.in_class
        self.in_class = True
        self.generic_visit(node)       # walk INTO the class body
        self.in_class = old_in_class   # restore when leaving class

    def visit_FunctionDef(self, node):
        """Only captures TOP-LEVEL functions, not methods"""
        if not self.in_class:
            self.functions.append({
                "name": node.name,
                "args": [
                    arg.arg for arg in node.args.args
                    if arg.arg != "self"   # skip 'self'
                ],
                "line": node.lineno,
            })
        self.generic_visit(node)

    def visit_Import(self, node):
        """Handles: import os, import numpy as np"""
        for alias in node.names:
            self.imports.append({
                "module": alias.name,    # "numpy"
                "alias": alias.asname,   # "np" or None
                "type": "import",
            })

    def visit_ImportFrom(self, node):
        """Handles: from fastapi import FastAPI"""
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "module": module,        # "fastapi"
                "name": alias.name,      # "FastAPI"
                "alias": alias.asname,
                "type": "from_import",
            })
        self.generic_visit(node)

    def _get_name(self, node):
        """Extract readable name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"


def analyze_file(code: str) -> Dict:
    """
    Main entry point. Takes raw Python code string,
    returns structured analysis dict.
    """
    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)

    return {
        "classes": analyzer.classes,
        "functions": analyzer.functions,
        "imports": analyzer.imports,
        "summary": {
            "total_classes": len(analyzer.classes),
            "total_functions": len(analyzer.functions),
            "total_imports": len(analyzer.imports),
            "complexity_score": (
                len(analyzer.classes) * 2 + len(analyzer.functions)
            ),
        },
    }