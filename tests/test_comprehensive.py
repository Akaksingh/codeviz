import unittest
import ast
import sys
import os
from unittest.mock import patch, MagicMock
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from parsers.python_parsers import CodeAnalyzer, analyze_file
from parsers.relationship_detector import RelationshipDetector
from generators.diagram_generator import (
    generate_class_diagram, 
    generate_dependency_graph,
    generate_component_diagram,
    generate_summary_text
)


class TestCodeAnalyzer(unittest.Test
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = CodeAnalyzer()
    
    def test_simple_class_detection(self):
        """Test detection of a simple class with methods"""
        code = '''
class TestClass:
    """A simple test class"""
    
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
    
    def _private_method(self):
        pass
    
    @property
    def display_name(self):
        return self.name.upper()
'''
        
        result = analyze_file(code, "test.py")
        
        
        self.assertEqual(len(result["classes"]), 1)
        class_data = result["classes"][0]
        self.assertEqual(class_data["name"], "TestClass")
        self.assertEqual(class_data["docstring"], "A simple test class")
        
        
        method_names = [method["name"] for method in class_data["methods"]]
        self.assertIn("__init__", method_names)
        self.assertIn("get_name", method_names) 
        self.assertIn("_private_method", method_names)
        self.assertIn("display_name", method_names)
        
        
        display_method = next(m for m in class_data["methods"] if m["name"] == "display_name")
        self.assertTrue(display_method["is_property"])
        
        self.assertEqual(len(result["functions"]), 0)
    
    def test_inheritance_detection(self):
        """Test detection of class inheritance"""
        code = '''
class Animal:
    def speak(self):
        pass

class Mammal(Animal):
    def breathe(self):
        pass

class Dog(Mammal):
    def bark(self):
        return "Woof!"

class Cat(Mammal):
    def meow(self):
        return "Meow!"
'''
        
        result = analyze_file(code, "test.py")
        
        # Check all classes detected
        class_names = [cls["name"] for cls in result["classes"]]
        self.assertIn("Animal", class_names)
        self.assertIn("Mammal", class_names)
        self.assertIn("Dog", class_names)
        self.assertIn("Cat", class_names)
        
        # Check inheritance relationships
        mammal_class = next(cls for cls in result["classes"] if cls["name"] == "Mammal")
        self.assertIn("Animal", mammal_class["bases"])
        
        dog_class = next(cls for cls in result["classes"] if cls["name"] == "Dog")
        self.assertIn("Mammal", dog_class["bases"])
    
    def test_function_vs_method_distinction(self):
        """Test that we correctly distinguish functions from methods"""
        code = '''
def standalone_function():
    """This is a standalone function"""
    return "hello"

async def async_function(param1: str, param2: int = 5) -> str:
    """An async function with type hints"""
    return f"{param1}: {param2}"

class MyClass:
    def class_method(self):
        """This is a class method"""
        return standalone_function()
    
    @staticmethod
    def static_method():
        return "static"
    
    @classmethod
    def class_method_decorator(cls):
        return cls

def another_function(param1, param2):
    return param1 + param2
'''
        
        result = analyze_file(code, "test.py")
        
        # Check functions
        self.assertEqual(len(result["functions"]), 3)
        function_names = [func["name"] for func in result["functions"]]
        self.assertIn("standalone_function", function_names)
        self.assertIn("async_function", function_names)
        self.assertIn("another_function", function_names)
        
        # Check async function detection
        async_func = next(f for f in result["functions"] if f["name"] == "async_function")
        self.assertTrue(async_func["is_async"])
        
        # Check type annotations
        self.assertIsNotNone(async_func["return_type"])
        
        # Check methods
        class_data = result["classes"][0]
        method_names = [method["name"] for method in class_data["methods"]]
        self.assertIn("class_method", method_names)
        self.assertIn("static_method", method_names)
        self.assertIn("class_method_decorator", method_names)
        
        # Check method decorators
        static_method = next(m for m in class_data["methods"] if m["name"] == "static_method")
        self.assertTrue(static_method["is_static"])
        
        # Ensure methods are NOT in functions
        self.assertNotIn("class_method", function_names)
        self.assertNotIn("static_method", function_names)
    
    def test_import_detection(self):
        """Test detection of various import types"""
        code = '''
import os
import sys
import json
from typing import Dict, List, Optional
from collections import defaultdict as dd
from pathlib import Path
from .local_module import LocalClass
'''
        
        result = analyze_file(code, "test.py")
        imports = result["imports"]
        
        # Check we found all imports
        self.assertEqual(len(imports), 9)  # os, sys, json, Dict, List, Optional, dd, Path, LocalClass
        
        # Check import types
        simple_imports = [imp for imp in imports if imp["type"] == "import"]
        from_imports = [imp for imp in imports if imp["type"] == "from_import"]
        
        self.assertEqual(len(simple_imports), 3)  # os, sys, json
        self.assertEqual(len(from_imports), 6)    # Dict, List, Optional, dd, Path, LocalClass
        
        # Check specific imports
        defaultdict_import = next(imp for imp in imports if imp.get("name") == "defaultdict")
        self.assertEqual(defaultdict_import["alias"], "dd")
        self.assertEqual(defaultdict_import["module"], "collections")
    
    def test_global_variables_detection(self):
        """Test detection of global variables and constants"""
        code = '''
API_VERSION = "1.0.0"
DEBUG_MODE = True
config: Dict[str, Any] = {}

class Config:
    def __init__(self):
        self.setting = "value"
'''
        
        result = analyze_file(code, "test.py")
        global_vars = result["global_variables"]
        
        self.assertEqual(len(global_vars), 3)
        
        var_names = [var["name"] for var in global_vars]
        self.assertIn("API_VERSION", var_names)
        self.assertIn("DEBUG_MODE", var_names)
        self.assertIn("config", var_names)
        
        # Check type annotation
        config_var = next(var for var in global_vars if var["name"] == "config")
        self.assertEqual(config_var["type"], "annotated_variable")
    
    def test_empty_file(self):
        """Test handling of empty Python file"""
        result = analyze_file("", "empty.py")
        
        self.assertEqual(len(result["classes"]), 0)
        self.assertEqual(len(result["functions"]), 0)
        self.assertEqual(len(result["imports"]), 0)
        self.assertEqual(result["summary"]["complexity_score"], 0)
    
    def test_syntax_error_handling(self):
        """Test that syntax errors are properly raised"""
        invalid_code = '''
class BrokenClass
    def broken_method()
        return "missing colons"
'''
        
        with self.assertRaises(SyntaxError):
            analyze_file(invalid_code, "broken.py")
    
    def test_complex_inheritance(self):
        """Test multiple inheritance and complex class hierarchies"""
        code = '''
class Mixin:
    def mixin_method(self):
        pass

class Base:
    def base_method(self):
        pass

class Child(Base, Mixin):
    def child_method(self):
        pass
'''
        
        result = analyze_file(code, "test.py")
        
        child_class = next(cls for cls in result["classes"] if cls["name"] == "Child")
        self.assertIn("Base", child_class["bases"])
        self.assertIn("Mixin", child_class["bases"])


class TestRelationshipDetector(unittest.TestCase):
    """
    Test the relationship detection functionality.
    """
    
    def setUp(self):
        self.detector = RelationshipDetector()
    
    def test_inheritance_detection(self):
        """Test detection of inheritance relationships"""
        code = '''
class Animal:
    pass

class Dog(Animal):
    def bark(self):
        pass

class Puppy(Dog):
    def play(self):
        pass
'''
        
        relationships = self.detector.analyze_relationships(code)
        inheritance = relationships["inheritance"]
        
        # Check inheritance relationships
        self.assertEqual(len(inheritance), 2)
        
        # Dog inherits from Animal
        dog_inheritance = next(rel for rel in inheritance if rel["child"] == "Dog")
        self.assertEqual(dog_inheritance["parent"], "Animal")
        
        # Puppy inherits from Dog
        puppy_inheritance = next(rel for rel in inheritance if rel["child"] == "Puppy")
        self.assertEqual(puppy_inheritance["parent"], "Dog")
    
    def test_function_call_detection(self):
        """Test detection of function call relationships"""
        code = '''
def helper_function():
    return "help"

def main_function():
    result = helper_function()
    return result

class MyClass:
    def method_one(self):
        return main_function()
    
    def method_two(self):
        return self.method_one()
'''
        
        relationships = self.detector.analyze_relationships(code)
        calls = relationships["calls"]
        
        self.assertTrue(len(calls) > 0)
        
        # Should detect main_function calling helper_function
        helper_call = any(call["to"] == "helper_function" for call in calls)
        self.assertTrue(helper_call)
    
    def test_composition_detection(self):
        """Test detection of composition relationships"""
        code = '''
class Engine:
    def start(self):
        pass

class Car:
    def __init__(self):
        self.engine = Engine()
    
    def start_car(self):
        return self.engine.start()
'''
        
        relationships = self.detector.analyze_relationships(code)
        composition = relationships["composition"]
        
        self.assertEqual(len(composition), 1)
        
        comp_rel = composition[0]
        self.assertEqual(comp_rel["container"], "Car")
        self.assertEqual(comp_rel["contained"], "Engine")
        self.assertEqual(comp_rel["attribute"], "engine")


class TestDiagramGeneration(unittest.TestCase):
    """
    Test diagram generation functionality.
    """
    
    def test_class_diagram_generation(self):
        """Test generation of Mermaid class diagram"""
        classes = [
            {
                "name": "Animal",
                "methods": [
                    {"name": "speak", "args": [], "is_async": False, "is_static": False, "is_property": False}
                ],
                "bases": []
            },
            {
                "name": "Dog", 
                "methods": [
                    {"name": "bark", "args": [], "is_async": False, "is_static": False, "is_property": False},
                    {"name": "fetch", "args": [{"name": "item"}], "is_async": False, "is_static": False, "is_property": False}
                ],
                "bases": ["Animal"]
            }
        ]
        
        relationships = {
            "inheritance": [
                {"child": "Dog", "parent": "Animal"}
            ]
        }
        
        diagram = generate_class_diagram(classes, relationships)
        
        # Check that Mermaid syntax is generated
        self.assertIn("classDiagram", diagram)
        self.assertIn("class Animal", diagram)
        self.assertIn("class Dog", diagram)
        self.assertIn("Animal <|-- Dog", diagram)  # Inheritance arrow
        self.assertIn("+speak()", diagram)
        self.assertIn("+bark()", diagram)
    
    def test_dependency_diagram_generation(self):
        """Test generation of Mermaid dependency diagram"""
        classes = [{"name": "MyClass"}]
        imports = [
            {"module": "os", "type": "import"},
            {"module": "json", "type": "import"},
            {"module": "fastapi", "type": "from_import", "name": "FastAPI"},
            {"module": "typing", "type": "from_import", "name": "Dict"}
        ]
        
        diagram = generate_dependency_graph(classes, imports)
        
        # Check that dependency diagram is generated
        self.assertIn("graph TD", diagram)
        self.assertIn("os", diagram)
        self.assertIn("json", diagram)
        self.assertIn("fastapi", diagram)
    
    def test_summary_text_generation(self):
        """Test generation of human-readable summary"""
        analysis = {
            "classes": [
                {"name": "Dog", "methods": [{"name": "bark"}]}
            ],
            "functions": [
                {"name": "main"}
            ],
            "imports": [
                {"module": "os"},
                {"module": "fastapi"}
            ],
            "relationships": {
                "inheritance": [],
                "composition": []
            },
            "summary": {
                "complexity_score": 15
            }
        }
        
        summary = generate_summary_text(analysis)
        
        # Check that summary contains expected information
        self.assertIn("1 class", summary)
        self.assertIn("1 top-level function", summary)
        self.assertIn("dependencies", summary)
        self.assertIn("complexity", summary)


class TestOriginalTestCases(unittest.TestCase):
    """
    Preserve the original test logic from the existing test file.
    """
    
    def setUp(self):
        self.SAMPLE_CODE = """
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
    
    def test_detects_classes(self):
        result = analyze_file(self.SAMPLE_CODE)
        class_names = [c["name"] for c in result["classes"]]
        
        self.assertIn("Animal", class_names)
        self.assertIn("Dog", class_names)
    
    def test_detects_methods(self):
        result = analyze_file(self.SAMPLE_CODE)
        dog = next(c for c in result["classes"] if c["name"] == "Dog")
        
        method_names = [m["name"] if isinstance(m, dict) else m for m in dog["methods"]]
        self.assertIn("speak", method_names)
        self.assertIn("fetch", method_names)
    
    def test_detects_inheritance(self):
        result = analyze_file(self.SAMPLE_CODE)
        dog = next(c for c in result["classes"] if c["name"] == "Dog")
        
        self.assertIn("Animal", dog["bases"])
    
    def test_methods_not_in_functions(self):
        """
        Key test - methods inside classes should NOT
        appear in top-level functions list
        """
        result = analyze_file(self.SAMPLE_CODE)
        function_names = [f["name"] for f in result["functions"]]
        
        self.assertNotIn("speak", function_names)
        self.assertNotIn("fetch", function_names)
        self.assertIn("create_animal", function_names)
    
    def test_detects_imports(self):
        result = analyze_file(self.SAMPLE_CODE)
        modules = [i["module"] for i in result["imports"]]
        
        self.assertIn("os", modules)
        self.assertIn("fastapi", modules)
    
    def test_summary_counts(self):
        result = analyze_file(self.SAMPLE_CODE)
        summary = result["summary"]
        
        self.assertEqual(summary["total_classes"], 2)
        self.assertEqual(summary["total_functions"], 1)


class TestIntegration(unittest.TestCase):
    """
    Integration tests that test the full pipeline.
    """
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis from code to diagram"""
        code = '''
from typing import List
import json

class Animal:
    """Base animal class"""
    def __init__(self, name: str):
        self.name = name
    
    def speak(self) -> str:
        raise NotImplementedError

class Dog(Animal):
    def speak(self) -> str:
        return f"{self.name} says Woof!"
    
    def fetch(self, item: str) -> str:
        return f"{self.name} fetches {item}"

def create_dog(name: str) -> Dog:
    return Dog(name)

def save_animal_data(animals: List[Animal]) -> None:
    data = [{"name": a.name} for a in animals]
    with open("animals.json", "w") as f:
        json.dump(data, f)
'''
        
        # Perform full analysis
        analysis = analyze_file(code, "test_integration.py")
        
        # Relationship detection
        tree = ast.parse(code)
        rel_detector = RelationshipDetector()
        rel_detector.visit(tree)
        
        # Generate diagrams
        class_diagram = generate_class_diagram(analysis["classes"], rel_detector.relationships)
        dependency_diagram = generate_dependency_graph(analysis["classes"], analysis["imports"])
        
        # Verify results
        self.assertEqual(len(analysis["classes"]), 2)
        self.assertEqual(len(analysis["functions"]), 2)
        self.assertIn("Animal <|-- Dog", class_diagram)
        self.assertIn("json", dependency_diagram)
        
        # Check inheritance relationship was detected
        inheritance = rel_detector.relationships["inheritance"]
        self.assertEqual(len(inheritance), 1)
        self.assertEqual(inheritance[0]["child"], "Dog")
        self.assertEqual(inheritance[0]["parent"], "Animal")


if __name__ == "__main__":
    # Run tests with verbose output
    print("\n🧪 Running Comprehensive CodeViz Tests...\n")
    unittest.main(verbosity=2)
