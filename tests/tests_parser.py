# tests/tests_parser.py

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from parsers.python_parsers import analyze_file

# ─────────────────────────────────────────
# SAMPLE CODE WE'LL USE TO TEST
# ─────────────────────────────────────────
SAMPLE_CODE = """
class Animal:
    def speak(self):
        pass
    def eat(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof"
    def fetch(self):
        return "Fetching!"

def create_animal(animal_type):
    if animal_type == "dog":
        return Dog()
    return Cat()

import os
from fastapi import FastAPI
"""

# ─────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────

def test_detects_classes():
    result = analyze_file(SAMPLE_CODE)
    class_names = [c["name"] for c in result["classes"]]
    
    assert "Animal" in class_names, "Should detect Animal class"
    assert "Dog" in class_names, "Should detect Dog class"
    print("✅ test_detects_classes passed")

def test_detects_methods():
    result = analyze_file(SAMPLE_CODE)
    dog = next(c for c in result["classes"] if c["name"] == "Dog")
    
    assert "speak" in dog["methods"], "Dog should have speak method"
    assert "fetch" in dog["methods"], "Dog should have fetch method"
    print("✅ test_detects_methods passed")

def test_detects_inheritance():
    result = analyze_file(SAMPLE_CODE)
    dog = next(c for c in result["classes"] if c["name"] == "Dog")
    
    assert "Animal" in dog["bases"], "Dog should inherit from Animal"
    print("✅ test_detects_inheritance passed")

def test_methods_not_in_functions():
    """
    Key test - methods inside classes should NOT
    appear in top-level functions list
    """
    result = analyze_file(SAMPLE_CODE)
    function_names = [f["name"] for f in result["functions"]]
    
    assert "speak" not in function_names, "speak() is a method, not a function"
    assert "fetch" not in function_names, "fetch() is a method, not a function"
    assert "create_animal" in function_names, "create_animal IS a top-level function"
    print("✅ test_methods_not_in_functions passed")

def test_detects_imports():
    result = analyze_file(SAMPLE_CODE)
    modules = [i["module"] for i in result["imports"]]
    
    assert "os" in modules, "Should detect 'import os'"
    assert "fastapi" in modules, "Should detect 'from fastapi import...'"
    print("✅ test_detects_imports passed")

def test_summary_counts():
    result = analyze_file(SAMPLE_CODE)
    summary = result["summary"]
    
    assert summary["total_classes"] == 2, f"Expected 2 classes, got {summary['total_classes']}"
    assert summary["total_functions"] == 1, f"Expected 1 function, got {summary['total_functions']}"
    print("✅ test_summary_counts passed")

def test_empty_file():
    """Edge case - what happens with empty file?"""
    result = analyze_file("")
    assert result["classes"] == [], "Empty file should have no classes"
    assert result["functions"] == [], "Empty file should have no functions"
    print("✅ test_empty_file passed")


# ─────────────────────────────────────────
# RUN ALL TESTS
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n🧪 Running CodeViz Tests...\n")
    
    test_detects_classes()
    test_detects_methods()
    test_detects_inheritance()
    test_methods_not_in_functions()
    test_detects_imports()
    test_summary_counts()
    test_empty_file()
    
    print("\n🎉 All tests passed!")